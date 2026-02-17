#!/usr/bin/env python3

"""Simplified profile route for debugging"""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
import logging
import traceback

def simplified_profile_route():
    """Simplified profile route for debugging"""
    try:
        # Log user info
        logging.info(f"Profile route accessed by user: {getattr(current_user, 'id', 'Unknown')}")
        
        # Basic user data that should always be available
        user_data = {
            'id': getattr(current_user, 'id', None),
            'email': getattr(current_user, 'email', 'Unknown'),
            'username': getattr(current_user, 'username', 'Unknown'),
            'is_authenticated': current_user.is_authenticated if current_user else False
        }
        
        # Basic stats
        user_stats = {
            'member_since': getattr(current_user, 'created_at', datetime.now()),
            'last_login': getattr(current_user, 'last_login', datetime.now()),
            'total_searches': getattr(current_user, 'total_searches', 0),
            'favorite_stocks': 0
        }
        
        # Try to get favorites safely
        user_favorites = []
        try:
            from app.models.favorites import Favorites
            if current_user and current_user.is_authenticated:
                user_favorites = Favorites.get_user_favorites(current_user.id)
                user_stats['favorite_stocks'] = len(user_favorites)
                logging.info(f"Successfully loaded {len(user_favorites)} favorites")
        except Exception as fav_error:
            logging.error(f"Could not load favorites: {fav_error}")
            user_favorites = []
        
        # Basic subscription status
        subscription_status = 'basic'
        try:
            if hasattr(current_user, 'has_subscription') and current_user.has_subscription:
                subscription_status = 'premium'
        except:
            pass
        
        # Basic referral stats
        referral_stats = {
            'referrals_made': 0,
            'referral_earnings': 0,
            'referral_code': f'REF{getattr(current_user, "id", "001")}'
        }
        
        # Basic preferences
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
        
        logging.info("Successfully prepared profile data, rendering template")
        
        return render_template('profile.html',
            user=current_user,
            subscription=None,
            subscription_status=subscription_status,
            user_stats=user_stats,
            user_language='nb',
            user_display_mode='light',
            user_number_format='norwegian',
            user_dashboard_widgets='[]',
            user_favorites=user_favorites,
            favorites=user_favorites,
            email_notifications=True,
            price_alerts=True,
            market_news=True,
            portfolio_updates=True,
            ai_insights=True,
            weekly_reports=True,
            referrals_made=0,
            referral_earnings=0,
            referral_code=f'REF{getattr(current_user, "id", "001")}',
            errors=None)
            
    except Exception as e:
        logging.error(f"Profile route error: {e}")
        logging.error(f"Profile route traceback: {traceback.format_exc()}")
        flash('Det oppstod en teknisk feil under lasting av profilen. Prøv igjen senere.', 'warning')
        return redirect(url_for('main.index'))

if __name__ == "__main__":
    print("Simplified profile route function created")
