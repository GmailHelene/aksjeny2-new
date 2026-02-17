from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from datetime import datetime, timedelta

EXEMPT_EMAILS = {'testuser@aksjeradar.trade', 'helene721@gmail.com', 'tonjekit91@gmail.com'}
TRIAL_PERIOD_DAYS = 0  # Set to 0 for testing, change to 10 for production
RESTRICTED_ROUTES = ['main.index', 'main.login', 'main.register', 'main.subscription', 'main.privacy', 'main.restricted_access']

def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn for å få tilgang.', 'warning')
            return redirect(url_for('main.login'))

        # Alltid gi tilgang til exempt users
        if hasattr(current_user, 'email') and current_user.email in EXEMPT_EMAILS:
            return f(*args, **kwargs)

        # Sjekk om brukeren har aktivt abonnement
        if current_user.has_active_subscription():
            return f(*args, **kwargs)

        # Sjekk prøveperiode
        if current_user.created_at:
            trial_end = current_user.created_at + timedelta(days=TRIAL_PERIOD_DAYS)
            if datetime.utcnow() <= trial_end:
                # Vis hvor mange dager som gjenstår av prøveperioden
                days_left = (trial_end - datetime.utcnow()).days + 1
                if days_left > 0:
                    flash(f'Du har {days_left} dager igjen av prøveperioden.', 'info')
                return f(*args, **kwargs)

        # Hvis ikke aktiv prøveperiode eller abonnement, redirect til subscription page
        flash('Du trenger et aktivt abonnement for å få tilgang.', 'warning')
        return redirect(url_for('main.subscription'))

    return decorated_function
