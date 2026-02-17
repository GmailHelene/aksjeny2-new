from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user
from ..utils.access_control import access_required
import logging
import random
from datetime import datetime, timedelta

demo = Blueprint('demo', __name__)
logger = logging.getLogger(__name__)

@demo.route('/')
def index():
    """Enhanced demo page with working functionality"""
    return render_template('demo.html',
                         title='Demo - Prøv Aksjeradar Gratis')

@demo.route('/api/demo-action', methods=['POST'])
def demo_action():
    """Handle demo button clicks and actions"""
    try:
        action = request.json.get('action')
        if not action:
            return jsonify({
                'success': False,
                'error': 'Ingen handling spesifisert'
            }), 400
            
        # Handle different demo actions
        response_data = handle_demo_action(action)
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error in demo action: {e}")
        return jsonify({
            'success': False,
            'error': 'En feil oppstod. Prøv igjen senere.'
        }), 500

def handle_demo_action(action):
    """Process different demo actions"""
    if action == 'ai_analysis':
        return generate_ai_analysis()
    elif action == 'graham':
        return generate_graham_analysis()
    elif action == 'buffett':
        return generate_buffett_analysis()
    elif action == 'short':
        return generate_short_analysis()
    elif action == 'screener':
        return generate_screener_demo()
    elif action == 'insider':
        return generate_insider_demo()
    elif action == 'portfolio':
        return generate_portfolio_demo()
    elif action == 'alerts':
        return generate_alerts_demo()
    else:
        raise ValueError(f"Unknown demo action: {action}")

def generate_ai_analysis(symbol='EQNR.OL'):
    """Generate AI analysis demo data"""
    return {
        'recommendation': random.choice(['KJØP', 'SELG', 'HOLD']),
        'confidence': random.randint(70, 95),
        'target_price_range': f"{random.randint(280, 320)}-{random.randint(330, 350)} NOK",
        'timeframe': '6-12 måneder',
        'signals': [
            {'icon': '✅', 'text': 'Sterk teknisk momentum'},
            {'icon': '✅', 'text': 'Økende institusjonell interesse'},
            {'icon': '✅', 'text': 'Positive fundamental faktorer'},
            {'icon': '⚠️', 'text': 'Økt volatilitet forventes'}
        ]
    }

def generate_graham_analysis():
    """Generate Graham analysis demo data"""
    return {
        'metrics': {
            'P/E Ratio': {'value': '12.5', 'status': 'success', 'comment': 'Under 15 ✓'},
            'P/B Ratio': {'value': '1.8', 'status': 'success', 'comment': 'Under 2.5 ✓'},
            'Debt/Equity': {'value': '0.6', 'status': 'warning', 'comment': 'Moderat'},
            'Graham Number': {'value': '285 NOK', 'status': 'success', 'comment': None}
        },
        'score': random.randint(7, 9),
        'recommendation': 'Value Opportunity',
        'recommendation_type': 'success'
    }

def generate_buffett_analysis():
    """Generate Buffett analysis demo data"""
    score = random.randint(75, 95)
    return {
        'criteria': [
            {'name': 'ROE', 'value': '18.5%', 'assessment': 'Høy', 'passed': True},
            {'name': 'Debt/Equity', 'value': '0.4', 'assessment': 'Lav', 'passed': True},
            {'name': 'Profit Margin', 'value': '22%', 'assessment': 'Sterk', 'passed': True},
            {'name': '10-år vekst', 'value': '12%', 'assessment': 'Konsistent', 'passed': True},
            {'name': 'P/E', 'value': '16.2', 'assessment': 'Akseptabel', 'passed': True}
        ],
        'quality_score': score,
        'quality_assessment': 'Kvalitetsselskap' if score >= 80 else 'Potensielt interessant',
        'recommendation': 'Anbefalt for langsiktige investorer',
        'recommendation_type': 'success' if score >= 80 else 'warning'
    }

def generate_short_analysis():
    """Generate short analysis demo data"""
    opportunity = random.choice([True, False])
    risk_score = random.randint(60, 90) if opportunity else random.randint(20, 40)
    return {
        'short_opportunity': opportunity,
        'recommendation': 'POTENSIELT SHORT' if opportunity else 'IKKE ANBEFALT SHORT',
        'signals': [
            {'icon': '🔻', 'text': 'Teknisk breakdown' if opportunity else 'Sterk teknisk støtte'},
            {'icon': '🔻', 'text': 'Svak fundamental utvikling' if opportunity else 'Solid fundamental'},
            {'icon': '🔻', 'text': 'Insider salg øker' if opportunity else 'Insider kjøp observert'}
        ],
        'risk_score': risk_score,
        'risk_assessment': 'Høy short-mulighet detektert' if opportunity else 'Lav short-potensiale'
    }

def generate_screener_demo():
    """Generate screener demo data"""
    return {
        'matches': [
            {'symbol': 'EQNR.OL', 'name': 'Equinor', 'score': 95},
            {'symbol': 'DNB.OL', 'name': 'DNB Bank', 'score': 88},
            {'symbol': 'TEL.OL', 'name': 'Telenor', 'score': 82}
        ],
        'criteria_matched': ['P/E < 15', 'ROE > 15%', 'Dividend Yield > 3%'],
        'total_matches': 3
    }

def generate_insider_demo():
    """Generate insider trading demo data"""
    return {
        'recent_trades': [
            {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'insider': 'John Doe',
                'position': 'Director',
                'type': 'Buy',
                'shares': 10000,
                'price': 285.50
            }
        ],
        'sentiment': 'Positive',
        'volume_trend': 'Increasing'
    }

def generate_portfolio_demo():
    """Generate portfolio optimization demo data"""
    return {
        'allocation': [
            {'symbol': 'EQNR.OL', 'weight': 30},
            {'symbol': 'DNB.OL', 'weight': 25},
            {'symbol': 'TEL.OL', 'weight': 20},
            {'symbol': 'MOWI.OL', 'weight': 15},
            {'symbol': 'NHY.OL', 'weight': 10}
        ],
        'expected_return': 12.5,
        'risk_level': 'Moderat',
        'sharpe_ratio': 1.8
    }

def generate_alerts_demo():
    """Generate alerts demo data"""
    return {
        'alerts': [
            {
                'type': 'PRICE',
                'symbol': 'EQNR.OL',
                'condition': 'above',
                'value': 300,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        ],
        'preferences': {
            'email': True,
            'push': True,
            'sms': False
        }
    }
