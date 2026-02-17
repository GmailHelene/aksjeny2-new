from flask import Flask, request, jsonify, render_template
from flask_login import login_required
import random

def init_advanced_analytics_routes(app):
    @app.route('/advanced-analytics/')
    @login_required
    def advanced_analytics():
        """Display advanced analytics page"""
        return render_template('advanced-analytics/index.html')

    @app.route('/advanced-analytics/generate-prediction', methods=['POST'])
    @login_required
    def generate_prediction():
        """Generate AI prediction for a ticker"""
        try:
            data = request.get_json()
            ticker = data.get('ticker', '').upper()
            
            if not ticker:
                return jsonify({'success': False, 'error': 'Ticker mangler'})
            
            # Generate demo prediction
            prediction = random.uniform(-10, 15)
            confidence = random.uniform(60, 95)
            
            result = f"Forventet prisendring: {prediction:+.2f}% med {confidence:.1f}% konfidens"
            
            return jsonify({
                'success': True,
                'result': result,
                'ticker': ticker,
                'prediction': prediction,
                'confidence': confidence
            })
        except Exception as e:
            app.logger.error(f"Prediction error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/advanced-analytics/batch-predictions', methods=['POST'])
    @login_required
    def batch_predictions():
        """Generate predictions for multiple tickers"""
        try:
            data = request.get_json()
            tickers = data.get('tickers', [])
            
            if not tickers:
                return jsonify({'success': False, 'error': 'Ingen tickers angitt'})
            
            results = []
            for ticker in tickers:
                prediction = random.uniform(-10, 15)
                results.append({
                    'ticker': ticker,
                    'prediction': prediction,
                    'signal': 'BUY' if prediction > 0 else 'SELL'
                })
            
            return jsonify({
                'success': True,
                'results': results
            })
        except Exception as e:
            app.logger.error(f"Batch prediction error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/advanced-analytics/market-analysis', methods=['POST'])
    @login_required
    def market_analysis():
        """Perform comprehensive market analysis"""
        try:
            # Generate demo analysis
            analysis = {
                'sentiment': 'Positiv',
                'volatility': 'Moderat',
                'trend': 'Bullish',
                'recommendation': 'Hold med forsiktig optimisme',
                'sectors': {
                    'energy': '+3.2%',
                    'finance': '+1.8%',
                    'tech': '-0.5%',
                    'healthcare': '+2.1%'
                }
            }
            
            analysis_text = f"""
            Markedet viser positive tegn med {analysis['sentiment'].lower()} sentiment.
            Volatiliteten er {analysis['volatility'].lower()}, som indikerer stabile forhold.
            Hovedtrenden er {analysis['trend'].lower()}.
            """
            
            return jsonify({
                'success': True,
                'analysis': analysis_text.strip(),
                'data': analysis
            })
        except Exception as e:
            app.logger.error(f"Market analysis error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})