"""
Norwegian error messages and user-friendly error handling
"""
from flask import jsonify, render_template, current_app
import logging

logger = logging.getLogger(__name__)

# Standard norske feilmeldinger
ERROR_MESSAGES = {
    'login_required': 'Du må logge inn for å få tilgang til denne siden.',
    'subscription_required': 'Du trenger et abonnement for å få tilgang til denne funksjonen.',
    'trial_expired': 'Din prøveperiode er utløpt. Oppgrader for å fortsette.',
    'invalid_credentials': 'Ugyldig brukernavn eller passord.',
    'user_not_found': 'Brukeren ble ikke funnet.',
    'email_exists': 'E-postadressen er allerede registrert.',
    'username_exists': 'Brukernavnet er allerede tatt.',
    'invalid_email': 'Ugyldig e-postadresse.',
    'password_too_short': 'Passordet må være minst 8 tegn langt.',
    'passwords_dont_match': 'Passordene stemmer ikke overens.',
    'invalid_stock_symbol': 'Ugyldig aksjesymbol.',
    'stock_not_found': 'Aksjen ble ikke funnet.',
    'portfolio_not_found': 'Porteføljen ble ikke funnet.',
    'invalid_quantity': 'Ugyldig antall aksjer.',
    'insufficient_data': 'Ikke nok data tilgjengelig.',
    'api_error': 'Det oppstod en feil med datakilden. Prøv igjen senere.',
    'network_error': 'Nettverksfeil. Sjekk internettforbindelsen din.',
    'server_error': 'Serverfeil. Prøv igjen senere.',
    'validation_error': 'Ugyldig data. Sjekk inndataene dine.',
    'permission_denied': 'Tilgang nektet.',
    'rate_limit_exceeded': 'For mange forespørsler. Vent litt før du prøver igjen.',
    'file_too_large': 'Filen er for stor.',
    'invalid_file_type': 'Ugyldig filtype.',
    'export_failed': 'Eksport feilet. Prøv igjen.',
    'import_failed': 'Import feilet. Sjekk filformatet.'
}

class UserFriendlyError(Exception):
    """Exception for user-friendly error messages"""
    
    def __init__(self, message_key, details=None, status_code=400):
        self.message_key = message_key
        self.details = details
        self.status_code = status_code
        super().__init__(ERROR_MESSAGES.get(message_key, message_key))

def get_error_message(key, default=None):
    """Get Norwegian error message by key"""
    return ERROR_MESSAGES.get(key, default or key)

def handle_api_error(error, endpoint=None):
    """Handle API errors with Norwegian messages"""
    logger.error(f"API Error in {endpoint}: {error}")
    
    if isinstance(error, UserFriendlyError):
        return jsonify({
            'success': False,
            'error': str(error),
            'error_code': error.message_key
        }), error.status_code
    
    # Generic error handling
    return jsonify({
        'success': False,
        'error': get_error_message('server_error'),
        'error_code': 'server_error'
    }), 500

def handle_form_error(error, form=None):
    """Handle form errors with Norwegian messages"""
    logger.error(f"Form Error: {error}")
    
    if isinstance(error, UserFriendlyError):
        return render_template('error.html', 
                             error_message=str(error),
                             error_code=error.message_key), error.status_code
    
    return render_template('error.html',
                         error_message=get_error_message('server_error'),
                         error_code='server_error'), 500

def format_number_norwegian(number):
    """Format numbers with Norwegian conventions"""
    if number is None:
        return '—'
    
    try:
        # Convert to float if it's not already
        num = float(number)
        
        # Format with space as thousands separator and comma as decimal
        if abs(num) >= 1000:
            return f"{num:,.2f}".replace(',', ' ').replace('.', ',')
        else:
            return f"{num:.2f}".replace('.', ',')
            
    except (ValueError, TypeError):
        return str(number)

def format_currency_norwegian(amount, currency='NOK'):
    """Format currency with Norwegian conventions"""
    if amount is None:
        return '—'
    
    try:
        formatted = format_number_norwegian(amount)
        return f"{formatted} {currency}"
    except:
        return f"{amount} {currency}"

def format_percentage_norwegian(percentage):
    """Format percentage with Norwegian conventions"""
    if percentage is None:
        return '—'
    
    try:
        num = float(percentage)
        formatted = format_number_norwegian(num)
        return f"{formatted}%"
    except:
        return f"{percentage}%"

def safe_api_call(func, *args, **kwargs):
    """Safely call API functions with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"API call failed: {e}")
        current_app.logger.error(f"API call failed: {e}")
        return None

def validate_stock_symbol(symbol):
    """Validate stock symbol format"""
    if not symbol:
        raise UserFriendlyError('invalid_stock_symbol')
    
    # Basic validation - can be extended
    if not symbol.isalnum() or len(symbol) < 1 or len(symbol) > 10:
        raise UserFriendlyError('invalid_stock_symbol')
    
    return symbol.upper()

def validate_quantity(quantity):
    """Validate stock quantity"""
    try:
        qty = float(quantity)
        if qty <= 0:
            raise UserFriendlyError('invalid_quantity')
        return qty
    except (ValueError, TypeError):
        raise UserFriendlyError('invalid_quantity')

def validate_email(email):
    """Basic email validation"""
    if not email or '@' not in email:
        raise UserFriendlyError('invalid_email')
    return email.lower()

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        raise UserFriendlyError('password_too_short')
    return password
