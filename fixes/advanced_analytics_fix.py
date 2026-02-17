from flask import Blueprint, render_template, jsonify, request
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import pandas as pd

advanced_analytics_bp = Blueprint('advanced_analytics', __name__)

@advanced_analytics_bp.route('/advanced-analytics')
def advanced_analytics():
    return render_template('advanced_analytics/index.html')

@advanced_analytics_bp.route('/api/generate-prediction', methods=['POST'])
def generate_prediction():
    try:
        ticker = request.json.get('ticker', 'AAPL')
        
        # Hent historisk data
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        if hist.empty:
            return jsonify({'error': 'Ingen data tilgjengelig'}), 400
        
        # Enkel moving average prediksjon
        prices = hist['Close'].values
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(prices) > 50 else sma_20
        
        # Enkel trend-basert prediksjon
        trend = (prices[-1] - prices[-20]) / prices[-20] if len(prices) > 20 else 0
        predicted_price = prices[-1] * (1 + trend * 0.5)  # Dempet trend
        
        prediction = {
            'ticker': ticker,
            'current_price': float(prices[-1]),
            'predicted_price': float(predicted_price),
            'confidence': 65 + np.random.randint(-10, 15),  # Mock confidence
            'timeframe': '30 dager',
            'trend': 'Bullish' if trend > 0 else 'Bearish',
            'support': float(min(prices[-20:])),
            'resistance': float(max(prices[-20:])),
            'sma_20': float(sma_20),
            'sma_50': float(sma_50)
        }
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_analytics_bp.route('/api/batch-predictions', methods=['POST'])
def batch_predictions():
    try:
        tickers = request.json.get('tickers', ['AAPL', 'MSFT', 'GOOGL'])
        predictions = []
        
        for ticker in tickers[:5]:  # Begrens til 5 for ytelse
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            if not hist.empty:
                prices = hist['Close'].values
                change = ((prices[-1] - prices[0]) / prices[0]) * 100
                
                predictions.append({
                    'ticker': ticker,
                    'current_price': float(prices[-1]),
                    'predicted_change': float(change * 0.7),  # Dempet prediksjon
                    'confidence': 60 + np.random.randint(-5, 20)
                })
        
        return jsonify({'predictions': predictions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_analytics_bp.route('/api/market-analysis', methods=['POST'])
def market_analysis():
    try:
        # Analyser hovedindekser
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ'
        }
        
        market_data = []
        for symbol, name in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            if not hist.empty:
                prices = hist['Close'].values
                volatility = np.std(prices) / np.mean(prices) * 100
                trend = (prices[-1] - prices[0]) / prices[0] * 100
                
                market_data.append({
                    'index': name,
                    'symbol': symbol,
                    'price': float(prices[-1]),
                    'change': float(trend),
                    'volatility': float(volatility),
                    'sentiment': 'Positive' if trend > 0 else 'Negative'
                })
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'market_sentiment': 'Bullish' if sum(d['change'] for d in market_data) > 0 else 'Bearish',
            'indices': market_data,
            'recommendation': 'Markedet viser positive tegn' if sum(d['change'] for d in market_data) > 0 else 'Vær forsiktig i dagens marked'
        }
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
