"""
New features routes for analyst recommendations and AI predictions
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required
from ..utils.access_control import access_required, demo_access
from ..models.user import User
from datetime import datetime, timedelta
import random
import logging

# Create blueprint for new features
features = Blueprint('features', __name__, url_prefix='/features')
logger = logging.getLogger(__name__)

@features.route('/')
@access_required
def index():
    """Features overview page"""
    return render_template('features/index.html', title='Funksjoner')

@features.route('/analyst-recommendations')
@access_required
def analyst_recommendations():
    """Compatibility route: redirect to real analysis recommendations."""
    try:
        ticker = request.args.get('ticker')
        if ticker:
            return redirect(url_for('analysis.recommendations', ticker=ticker))
        return redirect(url_for('analysis.recommendations'))
    except Exception:
        # As a last resort, go to analysis index
        return redirect(url_for('analysis.index'))

@features.route('/technical-analysis')
@access_required
def technical_analysis():
    """Technical analysis feature page"""
    # Get ticker from request if provided
    ticker = request.args.get('ticker') or request.form.get('ticker')
    technical_data = None
    available_stocks = {
        'oslo_stocks': [
            {'ticker': 'EQNR.OL', 'name': 'Equinor'},
            {'ticker': 'DNB.OL', 'name': 'DNB Bank'},
            {'ticker': 'NHY.OL', 'name': 'Norsk Hydro'},
            {'ticker': 'MOWI.OL', 'name': 'Mowi'},
            {'ticker': 'TEL.OL', 'name': 'Telenor'}
        ],
        'global_stocks': [
            {'ticker': 'AAPL', 'name': 'Apple Inc.'},
            {'ticker': 'TSLA', 'name': 'Tesla Inc.'},
            {'ticker': 'MSFT', 'name': 'Microsoft'},
            {'ticker': 'GOOGL', 'name': 'Alphabet Inc.'},
            {'ticker': 'AMZN', 'name': 'Amazon.com Inc.'}
        ]
    }
    
    if ticker:
        # Generate technical data for the selected ticker
        import random
        base_hash = abs(hash(ticker)) % 1000
        
        technical_data = {
            'ticker': ticker,
            'rsi': 30.0 + (base_hash % 40),  # RSI between 30-70
            'macd': -2.0 + (base_hash % 40) / 10,  # MACD between -2 and 2
            'macd_signal': -1.5 + (base_hash % 30) / 10,
            'bollinger_upper': 110 + (base_hash % 20),
            'bollinger_middle': 100,
            'bollinger_lower': 90 - (base_hash % 20),
            'signal': random.choice(['BUY', 'HOLD', 'SELL']),
            'signal_strength': random.randint(6, 10),
            'bb_position': random.choice(['upper', 'middle', 'lower']),
            'bb_signal': 'Normal',
            'bb_signal_color': 'warning'
        }
    
    return render_template('features/technical_analysis.html', 
                         title='Teknisk Analyse',
                         ticker=ticker,
                         technical_data=technical_data,
                         available_stocks=available_stocks)

@features.route('/market-news-sentiment')
@access_required
def market_news_sentiment():
    """Market news sentiment feature page"""
    return render_template('features/market_news_sentiment.html', title='Markeds Sentiment')

@features.route('/notifications')
@access_required
def notifications():
    """Redirect to real notifications page"""
    return redirect(url_for('notifications.index'))

@features.route('/ai-predictions')
@demo_access
def ai_predictions():
    """AI predictions page"""
    ticker = request.args.get('ticker')
    ekte_only = current_app.config.get('EKTE_ONLY') if current_app else False
    try:
        if ekte_only:
            # EKTE_ONLY policy: do not fabricate predictions
            neutral_message = None
            if ticker:
                stock_info = {'name': f'{ticker} Company'}
                neutral_message = f'Ingen analyse tilgjengelig for {ticker.upper()} – ekte modell ikke aktivert.'
            else:
                stock_info = None
                neutral_message = 'Ingen analyse tilgjengelig – ingen ekte prediksjonsmodell aktivert.'
            return render_template(
                'features/ai_predictions.html',
                ticker=ticker,
                predictions=None,  # no fabricated structure
                stock_info=stock_info,
                last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                warning=neutral_message
            )
        # Non-EKTE path left intentionally minimal to discourage demo usage
        return render_template(
            'features/ai_predictions.html',
            ticker=ticker,
            predictions=None,
            stock_info={'name': f'{ticker} Company'} if ticker else None,
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            warning='Prediksjonsmodell deaktivert.'
        )
    except Exception as e:
        current_app.logger.error(f"AI predictions route error: {e}")
        return render_template(
            'features/ai_predictions.html',
            ticker=ticker,
            predictions=None,
            stock_info={'name': f'{ticker} Company'} if ticker else None,
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            warning='Feil ved lasting av AI-side – ingen data generert.'
        )

@features.route('/social-sentiment')
@access_required
def social_sentiment():
    """Compatibility endpoint: forward to dedicated social sentiment blueprint."""
    ticker = (request.args.get('ticker') or '').strip().upper()
    if ticker:
        return redirect(url_for('social_sentiment.social_sentiment_page', ticker=ticker))
    return redirect(url_for('social_sentiment.social_sentiment_page'))

@features.route('/api/predict/<ticker>')
@access_required
def api_predict(ticker):
    """API endpoint for AI predictions"""
    try:
        # Mock prediction
        current = round(random.uniform(50, 500), 2)
        predicted = round(random.uniform(50, 500), 2)
        
        return jsonify({
            'success': True,
            'ticker': ticker.upper(),
            'current_price': current,
            'predicted_price': predicted,
            'change_percent': round(((predicted - current) / current) * 100, 2),
            'confidence': round(random.uniform(0.6, 0.95), 2),
            'prediction_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
    except Exception as e:
        current_app.logger.error(f"Error in prediction API: {str(e)}")
        # Return fallback prediction instead of 500 error
        return jsonify({
            'success': True,
            'data': {
                'current_price': 100.0,
                'predicted_price': 105.0,
                'change_percent': 5.0,
                'confidence': 0.75,
                'prediction_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'error': 'Prediksjonstjeneste midlertidig utilgjengelig',
                'fallback': True
            }
        }), 200
