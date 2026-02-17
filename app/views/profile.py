from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from flask import current_app
from ..models import Portfolio

def init_profile_routes(app):
    @app.route('/profile')
    @login_required
    def profile():
        try:
            user = current_user
            portfolios = Portfolio.query.filter_by(user_id=user.id).all()
            # --- Load additional context ---
            # Favorites
            try:
                from app.models.favorites import Favorites
                user_favorites = Favorites.get_user_favorites(user.id)
            except Exception:
                user_favorites = []
            # Subscription status
            try:
                subscription_status = user.subscription_type if hasattr(user, 'subscription_type') else 'free'
                subscription = getattr(user, 'subscription', None)
            except Exception:
                subscription_status = 'free'
                subscription = None
            # Referral code and stats
            try:
                referral_code = getattr(user, 'referral_code', user.username)
                referrals_made = getattr(user, 'referrals_made', 0)
                referral_earnings = getattr(user, 'referral_earnings', 0)
            except Exception:
                referral_code = user.username
                referrals_made = 0
                referral_earnings = 0
            # Preferences
            try:
                user_language = getattr(user, 'language', 'nb')
                user_display_mode = getattr(user, 'display_mode', 'auto')
                user_number_format = getattr(user, 'number_format', 'norwegian')
                user_dashboard_widgets = getattr(user, 'dashboard_widgets', '[]')
            except Exception:
                user_language = 'nb'
                user_display_mode = 'auto'
                user_number_format = 'norwegian'
                user_dashboard_widgets = '[]'
            # Notification settings
            try:
                email_notifications_enabled = getattr(user, 'email_notifications_enabled', False)
                price_alerts_enabled = getattr(user, 'price_alerts_enabled', False)
                market_news_enabled = getattr(user, 'market_news_enabled', False)
                portfolio_updates_enabled = getattr(user, 'portfolio_updates_enabled', False)
                ai_insights_enabled = getattr(user, 'ai_insights_enabled', False)
                weekly_reports_enabled = getattr(user, 'weekly_reports_enabled', False)
            except Exception:
                email_notifications_enabled = False
                price_alerts_enabled = False
                market_news_enabled = False
                portfolio_updates_enabled = False
                ai_insights_enabled = False
                weekly_reports_enabled = False
            # Errors (for template)
            errors = []
            # Render template with all context
            # Always pass all context variables, even if empty
            return render_template(
                'profile/profile.html',
                user=user,
                portfolios=portfolios or [],
                user_favorites=user_favorites or [],
                subscription_status=subscription_status or 'free',
                subscription=subscription,
                referral_code=referral_code or '',
                referrals_made=referrals_made or 0,
                referral_earnings=referral_earnings or 0,
                user_language=user_language or 'nb',
                user_display_mode=user_display_mode or 'auto',
                user_number_format=user_number_format or 'norwegian',
                user_dashboard_widgets=user_dashboard_widgets or '[]',
                email_notifications_enabled=email_notifications_enabled,
                price_alerts_enabled=price_alerts_enabled,
                market_news_enabled=market_news_enabled,
                portfolio_updates_enabled=portfolio_updates_enabled,
                ai_insights_enabled=ai_insights_enabled,
                weekly_reports_enabled=weekly_reports_enabled,
                errors=errors or []
            )
        except Exception as e:
            current_app.logger.error(f"Profile error: {str(e)}")
            flash('Kunne ikke laste profilen. Prøv igjen senere.', 'error')
            flash('Det oppstod en feil ved lasting av profilen. Prøv igjen senere.', 'error')
            return redirect(url_for('profile'))