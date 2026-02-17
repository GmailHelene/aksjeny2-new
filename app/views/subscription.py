from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/my-subscription')
@login_required
def my_subscription():
    """Display user's subscription details"""
    try:
        # Calculate renewal date if premium
        # Fallback/demo subscription object
        subscription = getattr(current_user, 'subscription', None)
        if not subscription or not getattr(subscription, 'is_active', False):
            class DemoSubscription:
                is_active = False
                plan = 'Gratis'
                end_date = None
            subscription = DemoSubscription()
        return render_template('subscription/my-subscription.html',
                             subscription=subscription)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Subscription page error: {str(e)}")
        flash('Kunne ikke laste abonnementsinformasjon', 'error')
        return redirect(url_for('index'))

@subscription_bp.route('/subscription/upgrade')
@login_required
def subscription_upgrade():
    """Redirect to upgrade page"""
    return render_template('subscription/upgrade.html')

@subscription_bp.route('/subscription/checkout/<plan>')
@login_required
def subscription_checkout(plan):
    """Handle subscription checkout"""
    plans = {
    'monthly': {'name': 'Månedlig', 'price': 299},
    'yearly': {'name': 'Årlig', 'price': 2499},
    'lifetime': {'name': 'Livstid', 'price': 9999}
    }
    
    if plan not in plans:
        flash('Ugyldig abonnementsplan', 'error')
        return redirect(url_for('my_subscription'))
    
    return render_template('subscription/checkout.html',
                         plan=plan,
                         plan_details=plans[plan])
