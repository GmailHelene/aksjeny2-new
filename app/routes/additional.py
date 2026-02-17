"""
Additional routes for missing endpoints
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user

additional_routes = Blueprint('additional', __name__)

@additional_routes.route('/subscription')
@additional_routes.route('/subscription/')
def subscription():
    """Subscription page"""
    return jsonify({
        'status': 'OK',
        'page': 'subscription',
        'message': 'Abonnement-side fungerer!',
        'plans': [
            {'name': 'Basic', 'price': '199 kr/mnd'},
            {'name': 'Pro', 'price': '249 kr/mnd'},
            {'name': 'Pro Årlig', 'price': '2499 kr/år'}
        ]
    })


@additional_routes.route('/privacy')
@additional_routes.route('/privacy/')
def privacy():
    """Privacy policy page"""
    return jsonify({
        'status': 'OK',
        'page': 'privacy',
        'message': 'Personvern-side fungerer!',
        'content': 'Personvernerklæring for Aksjeradar'
    })


