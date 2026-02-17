from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
try:
    from ..utils.access_control_unified import unified_access_required
except ImportError:
    # Fallback decorator if unified_access_required is not available
    def unified_access_required(f):
        return f

advanced_features = Blueprint('advanced_features', __name__, url_prefix='/advanced')

@advanced_features.route('/')
@login_required
@unified_access_required
def index():
    """Advanced Features main page"""
    return render_template('advanced_features/index.html', title='Advanced Features')

@advanced_features.route('/currency-converter')
@login_required
@unified_access_required
def currency_converter():
    """Currency converter tool"""
    from ..routes.dashboard import get_currency_rates
    rates = get_currency_rates()
    return render_template('advanced_features/currency_converter.html', title='Valutakonverter', rates=rates)

@advanced_features.route('/crypto-dashboard')
@login_required
@unified_access_required
def crypto_dashboard():
    """Crypto dashboard"""
    return render_template('advanced_features/crypto_dashboard.html', title='Crypto Dashboard')

@advanced_features.route('/tools')
@login_required
@unified_access_required
def tools():
    """Advanced tools"""
    return render_template('advanced_features/tools.html', title='Advanced Tools')
