from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import logging
import os

# Import access control
try:
    from ..utils.access_control import access_required
except ImportError:
    # Fallback decorator if access_control is not available
    def access_required(f):
        return f

# Import models and extensions
from ..models import User
from ..extensions import db

# Lazy import for stripe to handle missing dependency
def get_stripe():
    """Lazy import stripe to handle missing dependency"""
    try:
        import stripe
        return stripe
    except ImportError:
        return None

# Lazy import for ConsultantReportService
def get_consultant_report_service():
    """Lazy import ConsultantReportService to avoid circular imports"""
    try:
        from ..services.integrations import ConsultantReportService
        return ConsultantReportService
    except ImportError:
        return None

# Define pricing tiers and their limits
PRICING_TIERS = {
    'free': {
        'name': 'Gratis',
        'limits': {
            'daily_analyses': 3,
            'portfolio_stocks': 10,
            'price_alerts': 5,
            'export_reports': 1
        }
    },
    'basic': {
        'name': 'Basic',
        'limits': {
            'daily_analyses': 20,
            'portfolio_stocks': 50,
            'price_alerts': 25,
            'export_reports': 10
        }
    },
    'pro': {
        'name': 'Pro',
        'limits': {
            'daily_analyses': -1,  # Unlimited
            'portfolio_stocks': -1,
            'price_alerts': -1,
            'export_reports': -1
        }
    },
    'enterprise': {
        'name': 'Enterprise',
        'limits': {
            'daily_analyses': -1,
            'portfolio_stocks': -1,
            'price_alerts': -1,
            'export_reports': -1
        }
    }
}

pricing = Blueprint('pricing', __name__)
logger = logging.getLogger(__name__)

@pricing.route('/old-pricing')
@pricing.route('/pricing/')  
def index():
    """Redirect to main pricing page"""
    return redirect(url_for('pricing.pricing_page'))

@pricing.route('/', endpoint='pricing_page')
@pricing.route('', endpoint='pricing_page')
def pricing_page():
    """Main pricing page showing subscription plans"""
    try:
        # Define subscription plans
        plans = [
            {
                'name': 'Månedlig',
                'price': '249 kr/mnd',
                'price_yearly': None,
                'features': [
                    'Ubegrensede AI-analyser',
                    'Avansert porteføljeanalyse',
                    'Santtidsdata og realtidsoppdateringer',
                    'Full teknisk analyse',
                    'E-postvarsler og notifikasjoner',
                    'API-tilgang for utviklere'
                ],
                'color': 'primary',
                'recommended': True
            },
            {
                'name': 'Årlig',
                'price': '2499 kr/år', 
                'price_yearly': 'Spar 489 kr (208 kr/mnd)',
                'features': [
                    'Alt i månedlig plan +',
                    'Spar 17% sammenlignet med månedlig',
                    'Prioritert kundesupport',
                    'Eksklusive markedsrapporter',
                    'Beta-tilgang til nye funksjoner',
                    'Kun 208 kr/måned i gjennomsnitt',
                    'Porteføljeoptimalisering',
                    'Prioritert support'
                ],
                'color': 'success',
                'recommended': True
            },
            {
                'name': 'Enterprise',
                'price': 'Kontakt oss',
                'price_yearly': 'Tilpasset pris',
                'features': [
                    'Alt i Pro +',
                    'API-tilgang',
                    'Dedikert support',
                    'Tilpassede rapporter',
                    'Team-administrasjon',
                    'Prioritert databehandling'
                ],
                'color': 'dark',
                'recommended': False
            }
        ]
        
        # Check if user is authenticated and has a subscription
        user_subscription = None
        if current_user.is_authenticated:
            user_subscription = getattr(current_user, 'subscription_type', None)

        return render_template('pricing/pricing.html',
                             plans=plans,
                             user_subscription=user_subscription,
                             title='Priser og Abonnementer',
                             seo_title='Priser – Aksjeradar Pro | Ekte data og AI-verktøy',
                             seo_description='Velg Pro for ubegrensede analyser, sanntidsdata, insiderhandel og avanserte verktøy. Årlig plan med rabatt.')
                             
    except Exception as e:
        logger.error(f"Error in pricing page: {e}")
        flash('En feil oppstod ved lasting av prissiden.', 'error')
        return redirect(url_for('main.index'))

@pricing.route('/subscription')
@pricing.route('/subscription/')
def subscription():
    """Redirect to pricing page for consistency"""
    return redirect(url_for('pricing.index'))

@pricing.route('/upgrade/<tier>')
@login_required
def upgrade(tier):
    """Handle upgrade requests - redirect to Stripe checkout"""
    if tier not in ['monthly', 'yearly']:
        flash('Ugyldig abonnementstype.', 'error')
        return redirect(url_for('pricing.index'))
    
    # Redirect to stripe checkout with subscription type in URL
    return redirect(url_for('stripe.create_checkout_session', subscription_type=tier))

@pricing.route('/api/pricing/plans')
@access_required
def api_pricing_plans():
    """API endpoint for pricing plans"""
    try:
        plans = [
            {
                'id': 'monthly',
                'name': 'Månedlig',
                'price_monthly': 249,
                'price_yearly': None,
                'currency': 'NOK'
            },
            {
                'id': 'yearly',
                'name': 'Årlig',
                'price_monthly': None,
                'price_yearly': 2499,
                'currency': 'NOK'
            },
            {
                'id': 'enterprise',
                'name': 'Enterprise',
                'price_monthly': None,
                'price_yearly': None,
                'currency': 'NOK',
                'contact_sales': True
            }
        ]
        
        return jsonify({
            'status': 'OK',
            'plans': plans
        })
        
    except Exception as e:
        logger.error(f"Error in pricing API: {e}")
        return jsonify({
            'status': 'ERROR',
            'message': 'Kunne ikke hente prisplaner'
        }), 500
    if not tier_info.get('stripe_price_id'):
        flash('Dette abonnementet er ikke tilgjengelig for øyeblikket.', 'error')
        return redirect(url_for('pricing.pricing_page'))
    
    try:
        stripe_client = get_stripe()
        if not stripe_client:
            return jsonify({'error': 'Stripe ikke tilgjengelig'}), 503
        
        # Create Stripe checkout session
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{
                'price': tier_info['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('pricing.subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('pricing.pricing_page', _external=True),
            metadata={
                'user_id': current_user.id,
                'tier': tier
            }
        )
        
        return redirect(session.url, code=303)
        
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        flash('Det oppstod en feil ved opprettelse av betaling. Prøv igjen senere.', 'error')
        return redirect(url_for('pricing.pricing_page'))

@pricing.route('/subscription/success')
@login_required
def subscription_success():
    """Handle successful subscription"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Ugyldig sesjon.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        stripe_client = get_stripe()
        if not stripe_client:
            flash('Stripe ikke tilgjengelig', 'error')
            return redirect(url_for('main.index'))
            
        # Retrieve the session from Stripe
        session = stripe_client.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Safe metadata access
            tier = None
            if session.metadata:
                tier = session.metadata.get('tier')
            
            if tier and tier in PRICING_TIERS:
                current_user.subscription_tier = tier
                current_user.subscription_start = datetime.utcnow()
                current_user.subscription_end = datetime.utcnow() + timedelta(days=30)
                current_user.stripe_customer_id = session.customer
                db.session.commit()
                
                flash(f'Gratulerer! Du har oppgradert til {PRICING_TIERS[tier]["name"]}.', 'success')
            else:
                flash('Det oppstod en feil ved aktivering av abonnement.', 'error')
        else:
            flash('Betalingen ble ikke fullført.', 'warning')
            
    except Exception as e:
        logger.error(f"Subscription success error: {e}")
        flash('Det oppstod en feil ved bekrefting av abonnement.', 'error')
    
    return redirect(url_for('main.dashboard'))

@pricing.route('/buy-report', methods=['POST'])
@login_required
def buy_report():
    """Buy a single consultant report"""
    symbols = []
    if request.json:
        symbols = request.json.get('symbols', [])
    
    if not symbols or len(symbols) > 10:
        return jsonify({'error': 'Ugyldig aksje-liste'}), 400
    
    # Check if user has remaining free reports
    user_tier = get_user_tier()
    if PRICING_TIERS and user_tier:
        tier_info = PRICING_TIERS.get(user_tier, PRICING_TIERS.get('free', {}))
        # Ensure tier_info is always a dictionary
        if not isinstance(tier_info, dict):
            tier_info = {'report_limit': 0}
    else:
        tier_info = {'report_limit': 0}
    
    if isinstance(tier_info, dict):
        limits = tier_info.get('limits', {})
        if isinstance(limits, dict) and limits.get('consultant_reports', 0) > 0:
            # User has free reports remaining
            remaining = get_remaining_consultant_reports()
            if remaining > 0:
                return generate_and_deliver_report(symbols, free=True)
    
    # Create one-time payment for report
    try:
        stripe_client = get_stripe()
        if not stripe_client:
            return jsonify({'error': 'Stripe ikke tilgjengelig'}), 503
            
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{
                'price_data': {
                    'currency': 'nok',
                    'product_data': {
                        'name': f'AI Konsulent-rapport ({len(symbols)} aksjer)',
                        'description': f'Omfattende AI-analyse av: {", ".join(symbols[:3])}{"..." if len(symbols) > 3 else ""}',
                    },
                    'unit_amount': 249 * 100,  # 249 NOK in øre
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('pricing.report_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('main.dashboard', _external=True),
            metadata={
                'user_id': current_user.id,
                'symbols': ','.join(symbols),
                'type': 'consultant_report'
            }
        )
        
        return jsonify({'checkout_url': session.url})
        
    except Exception as e:
        logger.error(f"Report purchase error: {e}")
        # Return fallback instead of 500 error
        return jsonify({
            'success': False,
            'error': 'Betalingstjeneste midlertidig utilgjengelig. Prøv igjen senere.',
            'fallback': True
        }), 200

@pricing.route('/report/success')
@login_required
def report_success():
    """Handle successful report purchase"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Ugyldig sesjon.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        stripe_client = get_stripe()
        if not stripe_client:
            flash('Stripe ikke tilgjengelig', 'error')
            return redirect(url_for('main.dashboard'))
            
        session = stripe_client.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            symbols_str = getattr(session.metadata, 'symbols', '') if session.metadata else ''
            symbols = symbols_str.split(',') if symbols_str else []
            return generate_and_deliver_report(symbols, free=False)
        else:
            flash('Betalingen ble ikke fullført.', 'warning')
            
    except Exception as e:
        logger.error(f"Report success error: {e}")
        flash('Det oppstod en feil ved generering av rapport.', 'error')
    
    return redirect(url_for('main.dashboard'))

def generate_and_deliver_report(symbols: list, free: bool = False):
    """Generate and deliver consultant report"""
    try:
        # Get ConsultantReportService
        consultant_service = get_consultant_report_service()
        if not consultant_service:
            flash("Rapportgenerering ikke tilgjengelig", 'error')
            return redirect(url_for('main.dashboard'))
            
        # Generate PDF report
        filename = consultant_service.generate_pdf_report(symbols, current_user.id)
        
        if filename:
            # Update user's report usage if it was a free report
            if free:
                if not hasattr(current_user, 'reports_used_this_month'):
                    current_user.reports_used_this_month = 0
                current_user.reports_used_this_month += 1
                db.session.commit()
            
            flash(f'Rapporten har blitt generert! Last ned: {filename}', 'success')
        else:
            flash('Det oppstod en feil ved generering av rapport.', 'error')
            
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        flash('Det oppstod en feil ved generering av rapport.', 'error')
    
    return redirect(url_for('main.dashboard'))

@pricing.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    stripe_client = get_stripe()
    if not stripe_client:
        logger.error("Stripe ikke tilgjengelig")
        return '', 503
        
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')
    
    try:
        event = stripe_client.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        logger.error("Invalid payload")
        return '', 400
    except Exception as e:  # Generic exception for stripe errors
        logger.error(f"Stripe webhook error: {e}")
        return '', 400
    
    # Handle different event types
    if event['type'] == 'invoice.payment_succeeded':
        handle_subscription_payment_succeeded(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        handle_subscription_payment_failed(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_cancelled(event['data']['object'])
    
    return '', 200

def handle_subscription_payment_succeeded(invoice):
    """Handle successful subscription payment"""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            # Extend subscription
            if user.subscription_end and user.subscription_end > datetime.utcnow():
                user.subscription_end += timedelta(days=30)
            else:
                user.subscription_end = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            logger.info(f"Subscription renewed for user {user.email}")
            
    except Exception as e:
        logger.error(f"Error handling subscription payment: {e}")

def handle_subscription_payment_failed(invoice):
    """Handle failed subscription payment"""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            # Optionally send notification about failed payment
            logger.warning(f"Payment failed for user {user.email}")
            
    except Exception as e:
        logger.error(f"Error handling failed payment: {e}")

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_tier = 'free'
            user.subscription_end = datetime.utcnow()
            db.session.commit()
            logger.info(f"Subscription cancelled for user {user.email}")
            
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")

def get_user_tier():
    """Get current user's subscription tier"""
    if not current_user.is_authenticated:
        return 'free'
    
    if (hasattr(current_user, 'subscription_tier') and 
        current_user.subscription_tier and 
        current_user.subscription_tier != 'free'):
        
        # Check if subscription is still active
        if (hasattr(current_user, 'subscription_end') and 
            current_user.subscription_end and 
            current_user.subscription_end > datetime.utcnow()):
            return current_user.subscription_tier
    
    return 'free'

def get_tier_limits():
    """Get current user's tier limits"""
    tier = get_user_tier()
    return PRICING_TIERS.get(tier, PRICING_TIERS['free'])['limits']

def check_usage_limit(feature: str, amount: int = 1) -> bool:
    """Check if user can use a feature within their tier limits"""
    limits = get_tier_limits()
    
    if feature == 'daily_analyses':
        limit = limits.get('daily_analyses', 0)
        if limit == -1:  # Unlimited
            return True
        
        # Count today's analyses (you'll need to implement usage tracking)
        # For now, return True for simplicity
        return True
    
    elif feature == 'watchlist_size':
        limit = limits.get('watchlist_size', 0)
        if limit == -1:  # Unlimited
            return True
        
        # Count current watchlist items
        from app.models.watchlist import Watchlist
        current_count = Watchlist.query.filter_by(user_id=current_user.id).count()
        return current_count + amount <= limit
    
    elif feature == 'advanced_features':
        return limits.get('advanced_features', False)
    
    return False

def get_remaining_consultant_reports():
    """Get remaining free consultant reports for the month"""
    tier_limits = get_tier_limits()
    monthly_limit = tier_limits.get('consultant_reports', 0)
    
    if monthly_limit <= 0:
        return 0
    
    used_this_month = getattr(current_user, 'reports_used_this_month', 0)
    return max(0, monthly_limit - used_this_month)
