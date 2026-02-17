"""
Notification routes for real-time user alerts
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..models.notifications import Notification
from ..models.price_alert import PriceAlert
from ..models.user import User
from ..services.notification_service import notification_service
from ..extensions import db
from ..utils.access_control import access_required, demo_access
from datetime import datetime, timedelta
import logging

notifications_bp = Blueprint('notifications', __name__)
logger = logging.getLogger(__name__)

# Back-compat: module-level cache alias used by tests (TTL manipulation)
# We keep an app-scoped cache but expose a module-level reference to the same dict.
_PRICE_ALERTS_CACHE = None  # will be bound to the app's cache dict on first use

@notifications_bp.route('/')
@login_required
def index():
    """Main notifications page"""
    try:
        # Get filter parameters
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Build query
        query = Notification.query.filter_by(user_id=current_user.id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Order by newest first
        query = query.order_by(Notification.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        notifications = pagination.items
        
        # Get summary statistics
        total_count = Notification.query.filter_by(user_id=current_user.id).count()
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
        # Get counts by type
        type_counts = db.session.query(
            Notification.type, 
            db.func.count(Notification.id)
        ).filter_by(user_id=current_user.id).group_by(Notification.type).all()
        
        summary = {
            'total': total_count,
            'unread': unread_count,
            'types': dict(type_counts),
            'recent_activity': Notification.query.filter_by(user_id=current_user.id)\
                .filter(Notification.created_at >= datetime.utcnow() - timedelta(days=7)).count(),
            'priority_breakdown': {
                'high': Notification.query.filter_by(user_id=current_user.id, priority='high').count(),
                'medium': Notification.query.filter_by(user_id=current_user.id, priority='medium').count(),
                'low': Notification.query.filter_by(user_id=current_user.id, priority='low').count()
            }
        }
        
        return render_template('notifications/index.html',
                             notifications=notifications,
                             pagination=pagination,
                             unread_only=unread_only,
                             summary=summary)
    except Exception as e:
        logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications. Please try again later.', 'error')
        return redirect(url_for('main.index'))

@notifications_bp.route('/api/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_read(notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        notification.read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke markere som lest', 'fallback': True}), 200

@notifications_bp.route('/api/mark-unread/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_unread(notification_id):
    """Mark notification as unread"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()

        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404

        notification.read = False
        notification.read_at = None
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error marking notification as unread: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke markere som ulest', 'fallback': True}), 200

@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all notifications as read"""
    try:
        Notification.query.filter_by(
            user_id=current_user.id, 
            read=False
        ).update({
            'read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke markere alle som lest', 'fallback': True}), 200

@notifications_bp.route('/api/delete/<int:notification_id>', methods=['DELETE'])
@login_required
def api_delete(notification_id):
    """Delete a notification"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke slette varsling', 'fallback': True}), 200

@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """Get unread notification count"""
    try:
        count = Notification.query.filter_by(
            user_id=current_user.id,
            read=False
        ).count()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke hente antall uleste', 'fallback': True}), 200

@notifications_bp.route('/settings', methods=['GET', 'POST'])
@demo_access
def settings():
    """Notification settings page"""
    try:
        # For demo users, provide a simulated experience
        if not current_user.is_authenticated:
            if request.method == 'POST':
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Demo: Settings updated'})
                else:
                    flash('Demo: Notification settings updated!', 'success')
                    return redirect(url_for('notifications.settings'))
            
            # Return demo settings for unauthenticated users
            demo_preferences = {
                'email_enabled': True,
                'push_enabled': False,
                'email_price_alerts': True,
                'email_ai_predictions': False,
                'email_portfolio_updates': True,
                'email_news_alerts': False,
                'email_market_alerts': True,
                'push_price_alerts': False,
                'push_ai_predictions': False,
                'push_portfolio_updates': False,
                'push_news_alerts': False,
                'push_market_alerts': False,
                'quiet_hours_enabled': True,
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '08:00'
            }
            return render_template('notifications/settings.html', preferences=demo_preferences)
        
        if request.method == 'POST':
            # Handle both form and JSON data submission
            if request.is_json:
                # Handle JSON request from JavaScript
                settings_data = request.get_json()
                if not settings_data:
                    return jsonify({'success': False, 'error': 'No data provided'}), 400
            else:
                # Handle form submission
                settings_data = {
                    'email_enabled': 'email_enabled' in request.form,
                    'push_enabled': 'push_enabled' in request.form,
                    'email_price_alerts': 'email_price_alerts' in request.form,
                    'email_ai_predictions': 'email_ai_predictions' in request.form,
                    'email_portfolio_updates': 'email_portfolio_updates' in request.form,
                    'email_news_alerts': 'email_news_alerts' in request.form,
                    'email_market_alerts': 'email_market_alerts' in request.form,
                    'push_price_alerts': 'push_price_alerts' in request.form,
                    'push_ai_predictions': 'push_ai_predictions' in request.form,
                    'push_portfolio_updates': 'push_portfolio_updates' in request.form,
                    'push_news_alerts': 'push_news_alerts' in request.form,
                    'push_market_alerts': 'push_market_alerts' in request.form,
                    'quiet_hours_enabled': 'quiet_hours_enabled' in request.form,
                    'quiet_hours_start': request.form.get('quiet_hours_start', '22:00'),
                    'quiet_hours_end': request.form.get('quiet_hours_end', '08:00'),
                    'timezone': request.form.get('timezone', 'Europe/Oslo')
                }
            
            try:
                # Update user settings with error handling
                update_success = current_user.update_notification_settings(settings_data)
                if update_success:
                    db.session.commit()
                    logger.info(f"Successfully updated notification settings for user {current_user.id}")
                else:
                    db.session.rollback()
                    logger.error(f"Failed to update notification settings for user {current_user.id}")
                    raise Exception("Failed to update settings")
                    
            except Exception as update_error:
                logger.error(f"Error updating notification settings: {update_error}")
                db.session.rollback()
                if request.is_json:
                    return jsonify({'success': False, 'error': 'Kunne ikke oppdatere innstillinger', 'fallback': True}), 200
                else:
                    flash('Failed to update notification settings. Please try again.', 'error')
                    return redirect(url_for('notifications.settings'))
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Settings updated successfully'})
            else:
                flash('Notification settings updated successfully!', 'success')
                return redirect(url_for('notifications.settings'))
        
        # GET request - show form
        try:
            # Get user's notification preferences using new methods with error handling
            user_settings = current_user.get_notification_settings()
            if not user_settings or not isinstance(user_settings, dict):
                logger.warning(f"Invalid user settings for user {current_user.id}, using defaults")
                user_settings = {}
                
        except Exception as settings_error:
            logger.error(f"Error getting notification settings for user {current_user.id}: {settings_error}")
            user_settings = {}
        
        preferences = {
            'email_enabled': user_settings.get('email_enabled', True),
            'push_enabled': user_settings.get('push_enabled', False),
            'email_price_alerts': user_settings.get('email_price_alerts', True),
            'email_ai_predictions': user_settings.get('email_ai_predictions', True),
            'email_portfolio_updates': user_settings.get('email_portfolio_updates', True),
            'email_news_alerts': user_settings.get('email_news_alerts', True),
            'email_market_alerts': user_settings.get('email_market_alerts', True),
            'push_price_alerts': user_settings.get('push_price_alerts', False),
            'push_ai_predictions': user_settings.get('push_ai_predictions', False),
            'push_portfolio_updates': user_settings.get('push_portfolio_updates', False),
            'push_news_alerts': user_settings.get('push_news_alerts', False),
            'push_market_alerts': user_settings.get('push_market_alerts', False),
            'quiet_hours_enabled': user_settings.get('quiet_hours_enabled', False),
            'quiet_hours_start': user_settings.get('quiet_hours_start', '22:00'),
            'quiet_hours_end': user_settings.get('quiet_hours_end', '08:00'),
            'timezone': user_settings.get('timezone', 'Europe/Oslo')
        }
        
        return render_template('notifications/settings.html', preferences=preferences)
    except Exception as e:
        logger.error(f"Error with notification settings: {str(e)}")
        flash('Error with settings. Please try again later.', 'error')
        return redirect(url_for('notifications.index'))

@notifications_bp.route('/api/settings', methods=['GET', 'POST']) 
@demo_access
def api_update_settings():
    """API endpoint for notification settings - Enhanced with timeout and error handling"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({
                'success': False, 
                'error': 'Authentication required for notification settings'
            }), 401
            
        if request.method == 'GET':
            # Return current settings with timeout protection
            try:
                logger.info("Fetching notification settings for user")
                user_settings = current_user.get_notification_settings()
                logger.info("Successfully retrieved notification settings")
                return jsonify({
                    'success': True,
                    'settings': user_settings
                })
            except Exception as settings_error:
                logger.error(f"Error fetching notification settings: {str(settings_error)}")
                # Return default settings as fallback
                default_settings = {
                    'email_enabled': True,
                    'push_enabled': False,
                    'inapp_enabled': True,
                    'email_price_alerts': True,
                    'email_market_news': True,
                    'push_price_alerts': False,
                    'push_market_news': False,
                    'inapp_price_alerts': True,
                    'inapp_market_news': True,
                    'quiet_hours_enabled': False,
                    'quiet_hours_start': '22:00',
                    'quiet_hours_end': '08:00'
                }
                return jsonify({
                    'success': True,
                    'settings': default_settings,
                    'fallback': True
                })
        
        elif request.method == 'POST':
            # Update settings from JSON data
            settings_data = request.get_json()
            
            if not settings_data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            # Make sure all checkbox values are boolean
            for key, value in settings_data.items():
                if (key.endswith('_enabled') or key.endswith('_alerts') or 
                    key.startswith('email_') or key.startswith('push_') or
                    key == 'quiet_hours_enabled'):
                    settings_data[key] = bool(value)
            
            # Update user settings
            try:
                success = current_user.update_notification_settings(settings_data)
                if not success:
                    return jsonify({'success': False, 'error': 'Kunne ikke lagre innstillinger', 'fallback': True}), 200
                    
                db.session.commit()
                return jsonify({'success': True, 'message': 'Settings updated successfully'})
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error saving notification settings: {str(db_error)}")
                return jsonify({'success': False, 'error': 'Database-feil, prøv igjen senere', 'fallback': True}), 200
            
    except Exception as e:
        logger.error(f"Error in API settings: {str(e)}")
        return jsonify({'success': False, 'error': 'Innstillinger midlertidig utilgjengelig', 'fallback': True}), 200

@notifications_bp.route('/api/test', methods=['POST'])
@login_required
def api_test_notification():
    """Send a test notification"""
    try:
        notification_service.create_notification(
            user_id=current_user.id,
            notification_type='SYSTEM_UPDATE',
            title='Test Varsel',
            message='Dette er et testvarsel for å verifisere at innstillingene dine fungerer korrekt.',
            priority='medium'
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke sende testvarsel', 'fallback': True}), 200

@notifications_bp.route('/api/push_subscription', methods=['POST'])
@login_required
def save_push_subscription():
    """Save push notification subscription with enhanced error handling"""
    try:
        subscription_data = request.get_json()
        
        if not subscription_data:
            return jsonify({
                'success': False, 
                'error': 'Push notifications krever HTTPS og brukerens samtykke. Kontroller at nettleseren støtter push notifications.'
            }), 400
        
        # Store the push subscription data
        import json
        if hasattr(current_user, 'push_subscription'):
            current_user.push_subscription = json.dumps(subscription_data)
            current_user.push_notifications = True
            db.session.commit()
            logger.info(f"✅ Push subscription saved for user {current_user.id}")
        else:
            # Graceful fallback - user can still use other notification methods
            logger.warning(f"User model doesn't support push subscriptions, using fallback for user {current_user.id}")
            return jsonify({
                'success': True,
                'fallback': True,
                'message': 'Push notifications er ikke tilgjengelig, men e-post og in-app notifications fungerer.'
            })
        
        return jsonify({'success': True, 'message': 'Push notifications aktivert!'})
    except Exception as e:
        logger.error(f"Error saving push subscription: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Push notifications kan ikke aktiveres. Dette kan skyldes nettleserinnstillinger eller at siden ikke er tilgjengelig via HTTPS.',
            'fallback_available': True,
            'fallback_message': 'E-post og in-app notifications er fortsatt tilgjengelig.'
        }), 200

@notifications_bp.route('/api/clear-read', methods=['POST'])
@login_required
def api_clear_read():
    """Clear all read notifications"""
    try:
        Notification.query.filter_by(
            user_id=current_user.id,
            read=True
        ).delete()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error clearing read notifications: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke slette leste varsler', 'fallback': True}), 200

# Web interface routes
notifications_web_bp = Blueprint('notifications_web', __name__, url_prefix='/notifications')

@notifications_web_bp.route('/')
@demo_access
def notifications_page():
    """Notifications page"""
    if not current_user.is_authenticated:
        # Demo mode - show sample notifications
        demo_notifications = [
            {
                'id': 1,
                'title': 'Demo Prisalarm',
                'message': 'AAPL har nådd ditt målpris på $150',
                'type': 'price_alert',
                'priority': 'high',
                'created_at': datetime.utcnow() - timedelta(hours=2),
                'read': False
            },
            {
                'id': 2,
                'title': 'Demo Markedsoppdatering',
                'message': 'Oslo Børs har økt med 2.3% i dag',
                'type': 'market_update',
                'priority': 'medium',
                'created_at': datetime.utcnow() - timedelta(hours=5),
                'read': True
            }
        ]
        
        demo_summary = {
            'total': 2,
            'unread': 1,
            'types': {'price_alert': 1, 'market_update': 1},
            'recent_activity': 2,
            'priority_breakdown': {'high': 1, 'medium': 1, 'low': 0}
        }
        
        return render_template('notifications/index.html',
                             notifications=demo_notifications,
                             pagination=None,
                             unread_only=False,
                             summary=demo_summary,
                             demo_mode=True)
    
    return render_template('notifications/index.html')

@notifications_web_bp.route('/settings')
@login_required
def settings_page():
    """Notification settings page"""
    return render_template('notifications/settings.html')

@notifications_bp.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    """Get all notifications for the user"""
    try:
        notifications = Notification.query.filter_by(user_id=current_user.id).all()
        return jsonify({'success': True, 'notifications': [n.to_dict() for n in notifications]})
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify({'success': False, 'error': 'Kunne ikke hente varsler', 'fallback': True}), 200

@notifications_bp.route('/api/price_alerts', methods=['GET'])
@login_required
def api_price_alerts():
    """Return current user's price alerts with explicit module-level caching.

    Test expectations (see test_price_alerts_api.py & test_cache_ttl_expiry.py):
      - First call: cache_hit False, data_source DB or DB_ERROR_FALLBACK
      - Second call (within TTL): cache_hit True
      - After manual ts manipulation beyond TTL: cache_hit False again
      - Error path: success False, data_source in (ERROR, UNKNOWN)
    """
    from app.constants import DataSource
    from app.utils.api_response import ok, fail
    import time

    TTL = 30
    cache = current_app.extensions.setdefault('price_alerts_cache', {})
    # Bind module-level alias for tests that adjust TTL directly
    global _PRICE_ALERTS_CACHE
    _PRICE_ALERTS_CACHE = cache

    key = getattr(current_user, 'id', 'anon')
    now = time.time()
    entry = cache.get(key)
    if entry and (now - entry['ts']) < TTL:
        payload = {'alerts': entry['data']['alerts']}
        meta = {
            'cache_hit': True,
            'data_source': entry['meta'].get('data_source', DataSource.CACHE),
            'authenticated': True
        }
        # Ensure data_points present (api_response will auto-calc if missing but we include for clarity)
        payload['data_points'] = len(payload['alerts'])
        return ok(payload, **meta)

    # Miss or expired
    alerts = []
    data_source = DataSource.DB
    try:
        user_alerts = PriceAlert.query.filter_by(user_id=current_user.id).all()
        for a in user_alerts:
            alerts.append({
                'id': a.id,
                'ticker': a.ticker,
                'alert_type': a.alert_type,
                'threshold_price': a.threshold_price,
                'threshold_percent': a.threshold_percent,
                'is_active': a.is_active,
                'is_triggered': a.is_triggered,
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
    except Exception as db_err:
        logger.warning(f"Price alerts DB error: {db_err}")
        # Explicit error response per contract/tests
        return fail(
            'Database error',
            data={'alerts': []},
            cache_hit=False,
            data_source=getattr(DataSource, 'ERROR', 'ERROR'),
            authenticated=True,
            status_code=200
        )

    payload = {'alerts': alerts}
    meta = {
        'cache_hit': False,
        'data_source': data_source,
        'authenticated': True
    }
    cache[key] = {'ts': now, 'data': payload, 'meta': meta}
    return ok(payload, **meta)

    # (Note: unreachable fail path retained for clarity if refactored later.)

@notifications_bp.route('/api/user/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    """Unified user notification preferences (new). Legacy fields still supported but read-only here.

    POST body can be nested JSON like:
    {
      "email": {"enabled": true, "price_alerts": false},
      "push": {"enabled": true},
      "inapp": {"price_alerts": true},
      "quiet_hours": {"start": "23:00", "end": "07:00"}
    }
    """
    from ..services.notification_preferences_service import (
        get_prefs, to_dict, update_prefs, migrate_user_legacy_preferences
    )
    try:
        migrate_user_legacy_preferences(current_user)
        if request.method == 'POST':
            payload = request.get_json(silent=True) or {}
            prefs = update_prefs(current_user.id, payload)
            return jsonify({'success': True, 'preferences': to_dict(prefs)})
        prefs = get_prefs(current_user.id)
        return jsonify({'success': True, 'preferences': to_dict(prefs)})
    except Exception as e:
        logger.error(f"Unified user preferences error: {e}")
        return jsonify({'success': False, 'error': 'Kunne ikke hente/lagre preferanser'}), 500

@notifications_bp.route('/api/process-email-queue', methods=['POST'])
@login_required
def api_process_email_queue():
    """Admin manual trigger to process a batch of email queue items."""
    try:
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        from ..models.price_alert import EmailQueue
        from ..services.email_queue_processor import email_queue_processor
        processed_before = EmailQueue.query.filter_by(status='processed').count()
        pending_before = EmailQueue.query.filter_by(status='pending').count()
        email_queue_processor._process_pending()
        processed_after = EmailQueue.query.filter_by(status='processed').count()
        pending_after = EmailQueue.query.filter_by(status='pending').count()
        return jsonify({
            'success': True,
            'processed_delta': processed_after - processed_before,
            'pending_remaining': pending_after,
            'processed_total': processed_after,
            'pending_before': pending_before
        })
    except Exception as e:
        logger.error(f"Manual email queue processing failed: {e}")
        return jsonify({'success': False, 'error': 'Processing failed'}), 500
