from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings/delete-alert', methods=['POST'])
@login_required
def delete_price_alert():
    try:
        alert_id = request.form.get('alert_id')
        from app.models.price_alert import PriceAlert
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
        if alert:
            db.session.delete(alert)
            db.session.commit()
            flash('Prisvarsel slettet.', 'success')
        else:
            flash('Fant ikke prisvarsel.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Feil ved sletting av prisvarsel: {str(e)}', 'error')
    return redirect(url_for('settings'))
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings/delete-alert', methods=['POST'])
@login_required
def delete_price_alert():
    try:
        alert_id = request.form.get('alert_id')
        from app.models.price_alert import PriceAlert
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
        if alert:
            db.session.delete(alert)
            db.session.commit()
            flash('Prisvarsel slettet.', 'success')
        else:
            flash('Fant ikke prisvarsel.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Feil ved sletting av prisvarsel: {str(e)}', 'error')
    return redirect(url_for('settings'))

@settings_bp.route('/settings')
@login_required
def settings():
    """Display user settings page"""
    try:
        from app.models import UserSettings
        settings_obj = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings_obj:
            # Create demo settings if missing
            class DemoSettings:
                email_notifications = True
                push_notifications = False
                language = 'no'
                theme = 'light'
            settings_obj = DemoSettings()
        try:
            from app.models.price_alert import PriceAlert
            price_alerts = PriceAlert.query.filter_by(user_id=current_user.id).all()
        except Exception:
            price_alerts = []
        return render_template('settings/settings.html', 
                             user=current_user,
                             settings=settings_obj,
                             price_alerts=price_alerts)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Settings error: {str(e)}")
    flash('En feil oppstod ved lasting av innstillinger', 'error')
    return redirect(url_for('settings'))

@settings_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update user settings via AJAX"""
    try:
        setting = request.form.get('setting')
        value = request.form.get('value') == 'true'
        # Update the setting on the current_user if it exists
        if hasattr(current_user, setting):
            setattr(current_user, setting, value)
            try:
                db.session.commit()
                return jsonify({'success': True, 'message': 'Innstilling oppdatert'})
            except Exception as e:
                db.session.rollback()
                from flask import current_app
                current_app.logger.error(f"DB commit error: {str(e)}")
                return jsonify({'success': False, 'error': 'Kunne ikke lagre til databasen'}), 500
        else:
            return jsonify({'success': False, 'error': 'Ugyldig innstilling'}), 400
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f"Update settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
