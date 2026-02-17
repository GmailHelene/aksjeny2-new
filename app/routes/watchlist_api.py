"""
API routes for watchlist operations.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..extensions import csrf
from ..utils.symbol_utils import sanitize_symbol
from ..services.watchlist_service import WatchlistService
from ..utils.access_control import demo_access, access_required, api_access_required
import logging

watchlist_api = Blueprint('watchlist_api', __name__)
logger = logging.getLogger(__name__)

@watchlist_api.route('/api/watchlist/data')
@login_required
def get_watchlist_data():
    """Get watchlist data with real-time prices"""
    try:
        stocks = WatchlistService.get_watchlist_data(current_user.id)
        return jsonify({
            'success': True,
            'stocks': stocks
        })
    except Exception as e:
        logger.error(f"Error getting watchlist data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@watchlist_api.route('/api/watchlist/add', methods=['POST'])
@api_access_required
def add_to_watchlist_via_service():
    """Add stock to watchlist using WatchlistService (alternative endpoint)"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': 'Du må logge inn for å legge til favoritter'
            }), 401
            
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({
                'success': False,
                'error': 'Symbol er påkrevd'
            }), 400
            
        raw_symbol = data['symbol']
        symbol, valid = sanitize_symbol(raw_symbol)
        if not valid:
            return jsonify({'success': False, 'error': 'Ugyldig symbol'}), 400
        success, message = WatchlistService.add_to_watchlist(
            current_user.id,
            symbol,
            name=data.get('name')
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@watchlist_api.route('/api/watchlist/remove', methods=['POST'])
@login_required
def remove_from_watchlist():
    """Remove stock from watchlist"""
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({
                'success': False,
                'error': 'Symbol er påkrevd'
            }), 400
            
        raw_symbol = data['symbol']
        symbol, valid = sanitize_symbol(raw_symbol)
        if not valid:
            return jsonify({'success': False, 'error': 'Ugyldig symbol'}), 400
        success, message = WatchlistService.remove_from_watchlist(
            current_user.id,
            symbol
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@watchlist_api.route('/api/watchlist/update', methods=['POST'])
@login_required
def update_watchlist():
    """Update watchlist name and description"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Data er påkrevd'
            }), 400
            
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Navn er påkrevd'
            }), 400
        
        # Get user's default watchlist (assuming single watchlist for now)
        from ..models.watchlist import Watchlist
        from ..extensions import db
        
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
        if not watchlist:
            # Create new watchlist if none exists
            watchlist = Watchlist(
                user_id=current_user.id,
                name=name,
                description=description
            )
            db.session.add(watchlist)
        else:
            # Update existing watchlist
            watchlist.name = name
            watchlist.description = description
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Overvåkningsliste oppdatert'
        })
        
    except Exception as e:
        logger.error(f"Error updating watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@watchlist_api.route('/api/notifications', methods=['POST'])
@login_required
def update_notifications():
    """Update notification settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Data er påkrevd'
            }), 400
            
        enabled = data.get('enabled', False)
        
        # Update user notification settings
        if hasattr(current_user, 'notification_enabled'):
            current_user.notification_enabled = enabled
        
        from ..extensions import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Varsler aktivert' if enabled else 'Varsler deaktivert'
        })
        
    except Exception as e:
        logger.error(f"Error updating notifications: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@watchlist_api.route('/api/refresh', methods=['POST'])
@login_required
def refresh_watchlist_data():
    """Refresh stock data for watchlist"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', []) if data else []
        cleaned = []
        for s in symbols:
            cs, valid = sanitize_symbol(s)
            if valid:
                cleaned.append(cs)
        symbols = cleaned
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'Ingen symboler å oppdatere'
            }), 400
        
        # Get updated stock data
        stocks = WatchlistService.get_watchlist_data(current_user.id, symbols=symbols)
        
        return jsonify({
            'success': True,
            'stocks': stocks
        })
        
    except Exception as e:
        logger.error(f"Error refreshing watchlist data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
