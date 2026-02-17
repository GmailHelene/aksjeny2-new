
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app.utils.market_intel_utils import get_market_intelligence_data, get_analyst_coverage_data

# Opprett blueprint
external_data_bp = Blueprint('external_data', __name__)

@external_data_bp.route('/external-data/market-intelligence')
def market_intelligence():
    try:
        if current_user.is_authenticated:
            data = get_market_intelligence_data(real=True)
        else:
            data = get_market_intelligence_data(real=False)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = []
            
        return render_template('external_data/market_intelligence.html', data=data)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Market intelligence error: {str(e)}")
        # Fallback for errors with proper data structure
        data = [{'title': 'Market Intelligence', 'summary': 'Kunne ikke hente markedsdata. Vennligst prøv igjen senere.'}]
        return render_template('external_data/market_intelligence.html', data=data)

@external_data_bp.route('/external-data/analyst-coverage')
def analyst_coverage():
    try:
        # Return static data for testing in the correct format expected by template
        analyst_coverage = {
            'EQNR.OL': {
                'ratings': {'consensus': 'BUY', 'target_price': 320, 'num_analysts': 8},
                'consensus': {'recommendation': 'BUY'},
                'technical': {'trend': 'Bullish', 'support': 310, 'resistance': 340}
            },
            'DNB.OL': {
                'ratings': {'consensus': 'HOLD', 'target_price': 195, 'num_analysts': 6},
                'consensus': {'recommendation': 'HOLD'},
                'technical': {'trend': 'Neutral', 'support': 185, 'resistance': 205}
            },
            'TEL.OL': {
                'ratings': {'consensus': 'BUY', 'target_price': 165, 'num_analysts': 7},
                'consensus': {'recommendation': 'BUY'},
                'technical': {'trend': 'Bullish', 'support': 155, 'resistance': 175}
            },
            'MOWI.OL': {
                'ratings': {'consensus': 'BUY', 'target_price': 225, 'num_analysts': 9},
                'consensus': {'recommendation': 'BUY'},
                'technical': {'trend': 'Strong Bullish', 'support': 200, 'resistance': 240}
            },
            'NHY.OL': {
                'ratings': {'consensus': 'HOLD', 'target_price': 75, 'num_analysts': 5},
                'consensus': {'recommendation': 'HOLD'},
                'technical': {'trend': 'Neutral', 'support': 65, 'resistance': 80}
            },
            'YAR.OL': {
                'ratings': {'consensus': 'SELL', 'target_price': 45, 'num_analysts': 4},
                'consensus': {'recommendation': 'SELL'},
                'technical': {'trend': 'Bearish', 'support': 40, 'resistance': 50}
            }
        }
            
        return render_template('external_data/analyst_coverage.html', analyst_coverage=analyst_coverage)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Analyst coverage error: {str(e)}")
        # Return empty dict so template shows "No analyst coverage data available"
        return render_template('external_data/analyst_coverage.html', analyst_coverage={})
