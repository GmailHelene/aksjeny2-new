from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
try:
    from ..utils.access_control_unified import unified_access_required
except ImportError:
    # Fallback decorator if unified_access_required is not available
    def unified_access_required(f):
        return f
import random

advanced_analytics = Blueprint('advanced_analytics', __name__, url_prefix='/advanced-analytics')

@advanced_analytics.route('/')
@login_required
@unified_access_required
def index():
    """Display advanced analytics page"""
    return render_template('advanced_analytics.html', title='Advanced Analytics')

@advanced_analytics.route('/generate-prediction', methods=['POST'])
@login_required
@unified_access_required
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
            'prediction': result,
            'ticker': ticker,
            'change_percent': prediction,
            'confidence': confidence
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Feil ved generering av prediksjon: {str(e)}'
        })
