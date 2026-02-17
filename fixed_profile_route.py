from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

@main.route('/profile')
@login_required
def profile():
    """User profile page with simplified, robust error handling"""
    try:
        # Import required modules
        from ..models.user import User
        from ..models.favorites import Favorites
        from ..models.referral import Referral
        from ..extensions import db
        
        logger.info(f"Loading profile for user ID: {getattr(current_user, 'id', 'Unknown')}")
        
        # Initialize default values
        errors = []
        subscription_status = 'basic'
        user_stats = {
            'member_since': getattr(current_user, 'created_at', datetime.now()),
            'last_login': getattr(current_user, 'last_login', datetime.now()),
            'total_searches': getattr(current_user, 'total_searches', 0),
            'favorite_stocks': 0
        }
        user_favorites = []
        subscription = None
        
        # Subscription status - simplified
        try:
            if hasattr(current_user, 'email') and current_user.email in EXEMPT_EMAILS:
                subscription_status = 'premium'
            elif getattr(current_user, 'has_subscription', False):
                subscription_status = getattr(current_user, 'subscription_type', 'premium')
            elif getattr(current_user, 'trial_start', None) and not getattr(current_user, 'trial_used', True):
                subscription_status = 'trial'
        except Exception as e:
            logger.warning(f"Error checking subscription status: {e}")
            errors.append('subscription_check_failed')
        
        # Basic referral stats
        referral_stats = {
            'referrals_made': 0,
            'referral_earnings': 0,
            'referral_code': f'REF{getattr(current_user, "id", "001")}'
        }
        try:
            referrals = Referral.query.filter_by(referrer_id=current_user.id).count()
            referral_stats['referrals_made'] = referrals
            referral_stats['referral_earnings'] = referrals * 100
        except Exception as e:
            logger.warning(f"Error loading referral stats: {e}")
            errors.append('referral_stats_failed')
        
        # User preferences - simplified
        user_preferences = {
            'display_mode': 'light',
            'number_format': 'norwegian',
            'dashboard_widgets': '[]',
            'email_notifications': True,
            'price_alerts': True,
            'market_news': True,
            'portfolio_updates': True,
            'ai_insights': True,
            'weekly_reports': True
        }
        
        # SIMPLIFIED FAVORITES LOADING
        try:
            user_id = getattr(current_user, 'id', None)
            logger.info(f"Loading favorites for user ID: {user_id}")
            
            if user_id:
                favorites = Favorites.query.filter_by(user_id=user_id).all()
                logger.info(f"Found {len(favorites)} favorites for user {user_id}")
                
                for fav in favorites:
                    favorite_info = {
                        'symbol': fav.symbol,
                        'name': fav.name or fav.symbol,
                        'exchange': fav.exchange or 'Unknown',
                        'created_at': fav.created_at
                    }
                    user_favorites.append(favorite_info)
                
                user_stats['favorite_stocks'] = len(user_favorites)
        except Exception as e:
            logger.error(f"Error loading favorites: {e}")
            logger.error(traceback.format_exc())
            errors.append('favorites_failed')
        
        # Basic subscription info
        if subscription_status != 'basic' and subscription_status != 'free':
            try:
                subscription = {
                    'type': getattr(current_user, 'subscription_type', 'unknown'),
                    'start_date': getattr(current_user, 'subscription_start', None),
                    'end_date': getattr(current_user, 'subscription_end', None),
                    'is_trial': bool(getattr(current_user, 'trial_start', None) and not getattr(current_user, 'trial_used', True)),
                    'status': 'active' if subscription_status in ['premium', 'pro'] else 'inactive'
                }
            except Exception as e:
                logger.warning(f"Error getting subscription info: {e}")
                errors.append('subscription_info_failed')
        
        # Return complete template
        return render_template('profile.html',
            user=current_user,
            subscription=subscription,
            subscription_status=subscription_status,
            user_stats=user_stats,
            user_language=getattr(current_user, 'language', 'nb'),
            user_display_mode=user_preferences.get('display_mode', 'light'),
            user_number_format=user_preferences.get('number_format', 'norwegian'),
            user_dashboard_widgets=user_preferences.get('dashboard_widgets', '[]'),
            user_favorites=user_favorites,
            favorites=user_favorites,
            email_notifications=user_preferences.get('email_notifications', True),
            price_alerts=user_preferences.get('price_alerts', True),
            market_news=user_preferences.get('market_news', True),
            portfolio_updates=user_preferences.get('portfolio_updates', True),
            ai_insights=user_preferences.get('ai_insights', True),
            weekly_reports=user_preferences.get('weekly_reports', True),
            referrals_made=referral_stats.get('referrals_made', 0),
            referral_earnings=referral_stats.get('referral_earnings', 0),
            referral_code=referral_stats.get('referral_code', ''),
            errors=errors if errors else None)
    
    except Exception as e:
        logger.error(f"Critical error in profile page: {e}")
        logger.error(traceback.format_exc())
        flash('Det oppstod en teknisk feil under lasting av profilen. Prøv igjen senere.', 'warning')
        return redirect(url_for('main.index'))
