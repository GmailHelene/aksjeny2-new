from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, PriceAlert, UserSettings, Subscription

alerts_settings_bp = Blueprint('alerts_settings', __name__)

@alerts_settings_bp.route('/pro-tools/alerts', methods=['GET', 'POST'])
@login_required
def create_alert():
    if request.method == 'POST':
        try:
            # Fix: Remove browser_enabled from PriceAlert creation
            alert = PriceAlert(
                user_id=current_user.id,
                ticker=request.form.get('ticker'),
                target_price=float(request.form.get('target_price')),
                alert_type=request.form.get('alert_type', 'above'),
                email_enabled=request.form.get('email_enabled') == 'true',
                # Remove browser_enabled - it doesn't exist in model
                active=True
            )
            db.session.add(alert)
            db.session.commit()
            flash('Varsel opprettet!', 'success')
            return redirect(url_for('pro_tools.alerts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Kunne ikke opprette varsel: {str(e)}', 'error')
    
    return render_template('pro_tools/alerts.html')

@alerts_settings_bp.route('/price-alerts/create', methods=['GET', 'POST'])
@login_required
def create_price_alert():
    if request.method == 'POST':
        try:
            alert = PriceAlert(
                user_id=current_user.id,
                ticker=request.form.get('ticker'),
                target_price=float(request.form.get('target_price')),
                alert_type=request.form.get('alert_type', 'above'),
                email_enabled=True,
                active=True
            )
            db.session.add(alert)
            db.session.commit()
            flash('Prisvarsel opprettet!', 'success')
            return jsonify({'success': True, 'id': alert.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return render_template('price_alerts/create.html')

@alerts_settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
            db.session.commit()
        
        if request.method == 'POST':
            # Fix: Properly update settings
            user_settings.email_notifications = request.form.get('email_notifications') == 'on'
            user_settings.push_notifications = request.form.get('push_notifications') == 'on'
            user_settings.language = request.form.get('language', 'no')
            user_settings.theme = request.form.get('theme', 'light')
            
            db.session.commit()
            flash('Innstillinger oppdatert!', 'success')
            return redirect(url_for('alerts_settings.settings'))
        
        return render_template('settings.html', settings=user_settings)
    except Exception as e:
        db.session.rollback()
        return render_template('error.html', error=str(e)), 500

@alerts_settings_bp.route('/my-subscription')
@login_required
def my_subscription():
    try:
        subscription = Subscription.query.filter_by(user_id=current_user.id, active=True).first()
        
        if not subscription:
            # Create default free subscription
            subscription = {
                'plan': 'Free',
                'status': 'Active',
                'features': ['Grunnleggende analyser', 'Begrenset data', '5 varsler'],
                'price': 0
            }
        
        return render_template('subscription.html', subscription=subscription)
    except Exception as e:
        return render_template('error.html', error='Kunne ikke laste abonnementsinformasjon'), 500
