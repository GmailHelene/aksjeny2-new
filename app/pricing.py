"""
Pricing logic and utilities for Aksjeradar
"""
from flask import Blueprint, render_template, jsonify

pricing = Blueprint('pricing', __name__)

PRICING_PLANS = {
    'monthly': {
        'name': 'Månedlig',
        'price': 249,
        'currency': 'NOK',
        'period': 'month',
        'features': [
            'Ubegrensede AI-analyser',
            'Avansert porteføljeanalyse',
            'Santtidsdata',
            'Full teknisk analyse',
            'E-postvarsler',
            'API-tilgang'
        ]
    },
    'yearly': {
        'name': 'Årlig',
        'price': 2499,
        'currency': 'NOK',
        'period': 'year',
        'features': [
            'Alt i månedlig plan',
            'Spar 1489 kr per år',
            'Prioritert support',
            'Eksklusive rapporter',
            'Beta-tilgang'
        ]
    }
}
        'features': [
            'Alt i Pro',
            'Spar 27%',
            'Prioritert support',
            'Eksklusive rapporter'
        ]
    }
}

@pricing.route('/')
def index():
    """Pricing page"""
    return jsonify({
        'status': 'OK',
        'message': 'Pricing plans',
        'plans': PRICING_PLANS
    })