from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import app, db
from ..models import PriceAlert

@app.route('/pro-tools/alerts', methods=['GET', 'POST'])
@login_required
def alerts():
    if request.method == 'POST':
        try:
            alert = PriceAlert(
                user_id=current_user.id,
                ticker=request.form.get('ticker'),
                target_price=float(request.form.get('price')),
                alert_type=request.form.get('alert_type'),
                email_enabled=request.form.get('email_enabled') == 'on',
                active=True
            )
            db.session.add(alert)
            db.session.commit()
            flash('Varsel opprettet!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Kunne ikke opprette varsel: {str(e)}', 'error')
    
    alerts = PriceAlert.query.filter_by(user_id=current_user.id).all()
    return render_template('pro-tools/alerts.html', alerts=alerts)

@app.route('/price-alerts/create', methods=['GET', 'POST'])
@login_required
def price_alert_create():
    if request.method == 'POST':
        try:
            ticker = request.form.get('ticker')
            price = request.form.get('price')
            
            if not ticker or not price:
                flash('Ticker og pris må fylles ut', 'error')
                return render_template('price_alerts/create.html')
            
            alert = PriceAlert(
                user_id=current_user.id,
                ticker=ticker,
                price_threshold=float(price),
                alert_type=request.form.get('alert_type', 'above'),
                email_enabled=True,
                active=True
            )
            db.session.add(alert)
            db.session.commit()
            flash('Prisvarsel opprettet!', 'success')
            return redirect(url_for('alerts'))
        except Exception as e:
            db.session.rollback()
            flash('Kunne ikke opprette prisvarsel. Prøv igjen.', 'error')
    
    return render_template('price_alerts/create.html')