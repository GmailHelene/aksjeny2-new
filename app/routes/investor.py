from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_wtf.csrf import validate_csrf, ValidationError
from app.extensions import db
from app.models.user import User
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

investor = Blueprint('investor', __name__, url_prefix='/investor')

@investor.route('/')
def index():
    """Investor and acquisition opportunity page"""
    error_message = None
    try:
        total_users = User.query.count()
        premium_users = User.query.filter(
            User.subscription_type.in_(['monthly', 'yearly', 'lifetime', 'premium', 'pro'])
        ).count()
    except Exception as e:
        logger.error(f"Failed fetching investor metrics (DB): {e}")
        total_users = None
        premium_users = None
        # Updated wording (original placement before 'Markedsmulighet' was distracting)
        error_message = 'Brukertall oppdateres regelmessig – vises på nytt snart.'

    metrics = {
        'total_users': total_users,
        'premium_users': premium_users,
        'launch_date': '2024',
        'revenue_model': 'Subscription + Premium Features',
        'market_size': 'Norwegian Stock Market Analysis',
        'unique_features': [
            'Real-time Oslo Børs integration',
            'Advanced technical analysis tools',
            'Comprehensive screener functionality',
            'Community forum platform',
            'Portfolio management',
            'Price alerts and notifications'
        ]
    }
    return render_template('investor/index.html', metrics=metrics, metrics_error=error_message)

@investor.route('/overview')
def overview():
    """High-level platform overview page (authentic - no fabricated metrics).

    Shows structure, feature set, data sources, and growth enablers without
    inventing numbers. Any unavailable real metric is displayed as '—'.
    """
    # Attempt to gather a limited set of safe real counters
    total_users = None
    premium_users = None
    try:
        total_users = User.query.count()
        # subscription_active was renamed/removed; use subscription_type instead
        premium_users = User.query.filter(
            User.subscription_type.in_(['monthly', 'yearly', 'lifetime', 'premium', 'pro'])
        ).count()
    except Exception as e:
        logger.warning(f"Overview metrics degraded: {e}")

    feature_groups = [
        {
            'title': 'Kjernefunksjoner',
            'items': [
                'Porteføljeforvaltning',
                'Avanserte tekniske indikatorer',
                'Aksjescreener',
                'Varsler & notifikasjoner',
                'Favoritt- og overvåkningslister'
            ]
        },
        {
            'title': 'Data & Integrasjoner',
            'items': [
                'Oslo Børs kurser (sanntid / forsinket avhengig av feed)',
                'Historiske prisdata',
                'Selskapsnyheter',
                'Fundamentale nøkkeltall (pågående utvidelse)',
                'Tekniske mønstre (planlagt)'
            ]
        },
        {
            'title': 'Plattformarkitektur',
            'items': [
                'Modulær Flask / Python backend',
                'Caching-lag for eksterne forespørsler',
                'Skalerbar databasearkitektur',
                'Finkornet feature-gating via EKTE_ONLY',
                'Testdrevet autentisitetsregresjon'
            ]
        }
    ]

    context = {
        'total_users': total_users,
        'premium_users': premium_users,
        'feature_groups': feature_groups,
    }
    return render_template('investor/overview.html', **context)

@investor.route('/contact', methods=['POST'])
def contact():
    """Handle investor contact form submissions"""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError as e:
        logger.warning(f"CSRF validation failed (investor contact): {e}")
        flash('Sikkerhetsfeil: Vennligst prøv igjen.', 'error')
        return redirect(url_for('investor.index'))
    
    # Extract form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    company = request.form.get('company', '').strip()
    inquiry_type = request.form.get('inquiry_type', 'investment')
    message = request.form.get('message', '').strip()
    investment_range = request.form.get('investment_range', '')
    
    # Basic validation
    if not all([name, email, message]):
        flash('Navn, e-post og melding er påkrevd.', 'error')
        return redirect(url_for('investor.index'))
    
    try:
        # Log the inquiry
        logger.info(f"Investor inquiry from {name} ({email}) - Type: {inquiry_type}")
        
        # Send notification email (if configured)
        send_investor_notification(name, email, company, inquiry_type, message, investment_range)
        
        flash('Takk for din interesse! Vi tar kontakt innen 24 timer.', 'success')
        return redirect(url_for('investor.index'))
        
    except Exception as e:
        logger.error(f"Error processing investor contact: {e}")
        flash('En teknisk feil oppstod. Prøv igjen eller kontakt oss direkte.', 'error')
        return redirect(url_for('investor.index'))

def send_investor_notification(name, email, company, inquiry_type, message, investment_range):
    """Send notification email about investor inquiry via send_transactional."""
    try:
        from app.services.email_service import send_transactional
        recipient = os.getenv('INVESTOR_EMAIL', 'contact@aksjeradar.trade')
        body = f"""Ny investor/oppkjøper forespørsel:

Navn: {name}
E-post: {email}
Selskap: {company or 'Ikke oppgitt'}
Type forespørsel: {inquiry_type}
Investeringsområde: {investment_range or 'Ikke oppgitt'}

Melding:
{message}

Sendt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        ok = send_transactional(
            subject=f"Aksjeradar - Investor Inquiry: {inquiry_type.title()}",
            body=body,
            to_email=recipient,
        )
        if ok:
            logger.info(f"Investor notification sent for {name} ({email})")
        return ok
    except Exception as e:
        logger.error(f"Failed to send investor notification: {e}")
        return False