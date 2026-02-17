from datetime import datetime
from flask import Blueprint, jsonify, current_app, render_template, request
from flask_login import login_required, current_user
from ..models.watchlist import Watchlist, WatchlistItem
from ..models.favorites import Favorites
from ..extensions import db
from ..utils.access_control import access_required, demo_access
import re

watchlist = Blueprint('watchlist', __name__, url_prefix='/watchlist')

_TICKER_RE = re.compile(r'^[A-Z0-9][A-Z0-9\.-]{0,19}$')

def _valid_symbol(symbol: str) -> bool:
    if not symbol:
        return False
    symbol = symbol.strip().upper()
    return bool(_TICKER_RE.match(symbol))

def _watchlist_to_dict(wl: Watchlist, include_items: bool = True):
    payload = {
        'id': wl.id,
        'name': wl.name,
        'description': wl.description,
        'created_at': wl.created_at.isoformat() if wl.created_at else None,
        'updated_at': wl.updated_at.isoformat() if wl.updated_at else None,
        'item_count': len(wl.items) if hasattr(wl, 'items') else 0
    }
    if include_items:
        payload['items'] = [
            {
                'id': it.id,
                'symbol': it.symbol,
                'entry_price': it.entry_price,
                'notes': it.notes,
                'created_at': it.created_at.isoformat() if getattr(it, 'created_at', None) else None
            } for it in getattr(wl, 'items', [])
        ]
    return payload

@watchlist.route('/')
@access_required
def index():
    """Unified watchlist page with favorites migration (first visit)."""
    try:
        watchlists = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.updated_at.desc()).all()
        migrated = False
        if not watchlists:
            # Auto create default and migrate favorites
            default_wl = Watchlist(name='Mine favoritter', description='Automatisk opprettet', user_id=current_user.id)
            db.session.add(default_wl)
            db.session.flush()
            favs = Favorites.query.filter_by(user_id=current_user.id).all()
            for fav in favs:
                db.session.add(WatchlistItem(watchlist_id=default_wl.id, symbol=fav.symbol, notes=fav.name))
            db.session.commit()
            watchlists = [default_wl]
            migrated = True
        return render_template(
            'watchlist/index.html',
            watchlists=watchlists,
            migrated=migrated,
            title='Mine Watchlists',
            description='Følg dine favorittaksjer med intelligente varsler'
        )
    except Exception as e:
        current_app.logger.error(f"Error loading watchlist page: {e}")
        return render_template(
            'errors/error.html',
            message='Beklager, watchlist-siden er midlertidig utilgjengelig.',
            title='Watchlist Utilgjengelig'
        ), 200

@watchlist.route('/<int:id>')
@access_required
def view_watchlist(id):
    """View individual watchlist"""
    try:
        watchlist_obj = None
        
        # Get specific watchlist if user is authenticated
        if current_user.is_authenticated:
            try:
                from ..models.watchlist import Watchlist, WatchlistStock
                watchlist_obj = Watchlist.query.filter_by(id=id, user_id=current_user.id).first()
                
                if not watchlist_obj:
                    # Try to find any watchlist for demo purposes
                    watchlist_obj = Watchlist.query.filter_by(user_id=current_user.id).first()
                    
            except Exception as e:
                current_app.logger.error(f"Error fetching watchlist {id}: {e}")
        

        # Only show real user data, no demo logic
        stocks = []
        try:
            if hasattr(watchlist_obj, 'stocks') and watchlist_obj.stocks:
                from ..services.data_service import DataService
                data_service = DataService()
                for stock in watchlist_obj.stocks:
                    try:
                        stock_info = data_service.get_stock_info(stock.symbol)
                        if stock_info:
                            stocks.append({
                                'symbol': stock.symbol,
                                'name': stock_info.get('name', stock.symbol),
                                'price': stock_info.get('last_price', 0),
                                'change': stock_info.get('change', 0),
                                'change_percent': stock_info.get('change_percent', 0),
                                'volume': stock_info.get('volume', 0)
                            })
                    except Exception as stock_error:
                        current_app.logger.warning(f"Error getting stock info for {stock.symbol}: {stock_error}")
        except Exception as stocks_error:
            current_app.logger.error(f"Error loading stocks for watchlist {id}: {stocks_error}")
            stocks = []
        return render_template('watchlist/detail.html',
                             watchlist=watchlist_obj,
                             stocks=stocks,
                             title=f"Watchlist: {watchlist_obj.name}",
                             description=f"Detaljer for {watchlist_obj.name}")
    except Exception as e:
        current_app.logger.error(f"Error loading watchlist {id}: {e}")
        return render_template('errors/error.html',
                             message="Kunne ikke laste watchlist. Prøv igjen senere.",
                             title="Watchlist Error"), 200

@watchlist.route('/delete/<int:id>', methods=['POST'])
@access_required
def delete_watchlist(id):
    """Delete a watchlist and all its items."""
    try:
        wl = Watchlist.query.filter_by(id=id, user_id=current_user.id).first()
        if not wl:
            return jsonify({'success': False, 'error': 'Watchlist ikke funnet'}), 404
        db.session.delete(wl)
        db.session.commit()
        return jsonify({'success': True, 'deleted': id})
    except Exception as e:
        current_app.logger.error(f"Error deleting watchlist {id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Kunne ikke slette watchlist'}), 500

# ---- JSON API CRUD ----
@watchlist.route('/api', methods=['GET'])
@login_required
def api_list_watchlists():
    wls = Watchlist.query.filter_by(user_id=current_user.id).all()
    return jsonify({'success': True, 'watchlists': [_watchlist_to_dict(w) for w in wls]})

@watchlist.route('/api', methods=['POST'])
@login_required
def api_create_watchlist():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not 1 < len(name) <= 80:
        return jsonify({'success': False, 'error': 'Ugyldig navn'}), 400
    existing = Watchlist.query.filter(Watchlist.user_id==current_user.id, db.func.lower(Watchlist.name)==name.lower()).first()
    if existing:
        return jsonify({'success': True, 'watchlist': _watchlist_to_dict(existing), 'duplicate': True})
    wl = Watchlist(name=name, user_id=current_user.id)
    db.session.add(wl)
    db.session.commit()
    return jsonify({'success': True, 'watchlist': _watchlist_to_dict(wl)}) ,201

@watchlist.route('/api/<int:watchlist_id>/items', methods=['POST'])
@login_required
def api_add_item(watchlist_id):
    data = request.get_json(silent=True) or {}
    symbol = (data.get('symbol') or '').upper().strip()
    if not _valid_symbol(symbol):
        return jsonify({'success': False, 'error': 'Ugyldig ticker'}), 400
    wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
    if not wl:
        return jsonify({'success': False, 'error': 'Watchlist ikke funnet'}), 404
    existing = WatchlistItem.query.filter_by(watchlist_id=wl.id, symbol=symbol).first()
    if existing:
        return jsonify({'success': True, 'item': {'id': existing.id, 'symbol': existing.symbol}, 'duplicate': True})
    item = WatchlistItem(watchlist_id=wl.id, symbol=symbol)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item': {'id': item.id, 'symbol': item.symbol}}), 201

@watchlist.route('/api/<int:watchlist_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
def api_remove_item(watchlist_id, item_id):
    wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
    if not wl:
        return jsonify({'success': False, 'error': 'Watchlist ikke funnet'}), 404
    item = WatchlistItem.query.filter_by(id=item_id, watchlist_id=wl.id).first()
    if not item:
        return jsonify({'success': False, 'error': 'Element ikke funnet'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'removed': item_id})

@watchlist.route('/api/<int:watchlist_id>', methods=['DELETE'])
@login_required
def api_delete_watchlist(watchlist_id):
    wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
    if not wl:
        return jsonify({'success': False, 'error': 'Watchlist ikke funnet'}), 404
    db.session.delete(wl)
    db.session.commit()
    return jsonify({'success': True, 'deleted': watchlist_id})

@watchlist.route('/api/<int:watchlist_id>', methods=['PATCH'])
@login_required
def api_update_watchlist(watchlist_id):
    """Partial update of a watchlist (currently supports name & description)."""
    data = request.get_json(silent=True) or {}
    wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
    if not wl:
        return jsonify({'success': False, 'error': 'Watchlist ikke funnet'}), 404
    name = data.get('name')
    description = data.get('description')
    updated = False
    if name is not None:
        name = name.strip()
        if not 1 < len(name) <= 80:
            return jsonify({'success': False, 'error': 'Ugyldig navn'}), 400
        # uniqueness check (case-insensitive)
        exists = Watchlist.query.filter(Watchlist.user_id==current_user.id, db.func.lower(Watchlist.name)==name.lower(), Watchlist.id!=wl.id).first()
        if exists:
            return jsonify({'success': False, 'error': 'Navn allerede i bruk'}), 409
        wl.name = name
        updated = True
    if description is not None:
        wl.description = (description or '').strip() or None
        updated = True
    if updated:
        wl.updated_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'success': True, 'watchlist': _watchlist_to_dict(wl)})

@watchlist.route('/api/<int:watchlist_id>/detail', methods=['GET'])
@login_required
def api_watchlist_detail(watchlist_id):
    """Return watchlist with enriched item quote data (graceful fallbacks)."""
    wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
    if not wl:
        return jsonify({'success': False, 'error': 'Watchlist ikke funnet'}), 404
    base = _watchlist_to_dict(wl, include_items=False)
    enriched_items = []
    # Attempt quote enrichment
    try:
        from ..services.data_service import DataService
        ds = DataService()
    except Exception:
        ds = None
    for it in wl.items:
        item_payload = {
            'id': it.id,
            'symbol': it.symbol,
            'notes': it.notes,
            'created_at': it.created_at.isoformat() if getattr(it, 'created_at', None) else None
        }
        if ds:
            try:
                q = ds.get_stock_info(it.symbol)
                if q:
                    item_payload.update({
                        'price': q.get('last_price'),
                        'change': q.get('change'),
                        'change_percent': q.get('change_percent')
                    })
            except Exception:
                # Silent fallback; keep base item data
                pass
        else:
            # Demo fallback values
            item_payload.update({'price': None, 'change': None, 'change_percent': None})
        enriched_items.append(item_payload)
    base['items'] = enriched_items
    return jsonify({'success': True, 'watchlist': base})

def _get_or_create_default_watchlist(user_id):
    wl = Watchlist.query.filter_by(user_id=user_id).order_by(Watchlist.created_at.asc()).first()
    if not wl:
        wl = Watchlist(name='Mine favoritter', description='Auto generert', user_id=user_id)
        db.session.add(wl)
        db.session.commit()
    return wl

@watchlist.route('/api/toggle', methods=['POST'])
@login_required
def api_toggle_symbol():
    """Toggle symbol presence in the user's default watchlist and mirror Favorites.
    Returns JSON with action: 'added' or 'removed'."""
    data = request.get_json(silent=True) or {}
    symbol = (data.get('symbol') or '').strip().upper()
    if not _valid_symbol(symbol):
        return jsonify({'success': False, 'error': 'Ugyldig ticker'}), 400
    wl = _get_or_create_default_watchlist(current_user.id)
    existing = WatchlistItem.query.filter_by(watchlist_id=wl.id, symbol=symbol).first()
    action = None
    try:
        if existing:
            db.session.delete(existing)
            action = 'removed'
            # Mirror remove in Favorites
            fav = Favorites.query.filter_by(user_id=current_user.id, symbol=symbol).first()
            if fav:
                db.session.delete(fav)
        else:
            item = WatchlistItem(watchlist_id=wl.id, symbol=symbol)
            db.session.add(item)
            action = 'added'
            # Mirror add in Favorites if not present
            if not Favorites.query.filter_by(user_id=current_user.id, symbol=symbol).first():
                db.session.add(Favorites(user_id=current_user.id, symbol=symbol, name=symbol))
        db.session.commit()
        return jsonify({'success': True, 'symbol': symbol, 'action': action, 'watchlist_id': wl.id})
    except Exception as e:
        current_app.logger.error(f"Toggle symbol error {symbol}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Kunne ikke oppdatere symbol'}), 500
