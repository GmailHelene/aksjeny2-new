from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
try:
    from ..utils.access_control_unified import unified_access_required
except ImportError:
    # Fallback decorator if unified_access_required is not available
    def unified_access_required(f):
        return f

pro_tools = Blueprint('pro_tools', __name__, url_prefix='/pro-tools')

@pro_tools.route('/')
@login_required
@unified_access_required
def index():
    """Pro Tools main page"""
    return render_template('main/pro_tools.html', title='Pro Tools')

@pro_tools.route('/advanced-analytics')
@login_required
@unified_access_required
def advanced_analytics():
    """Redirect to advanced analytics"""
    return redirect(url_for('advanced_analytics.index'))

@pro_tools.route('/currency-converter')
@login_required
@unified_access_required
def currency_converter():
    """Redirect to currency converter"""
    return redirect(url_for('advanced_features.currency_converter'))

@pro_tools.route('/investment-analyzer')
@login_required
@unified_access_required
def investment_analyzer():
    """Redirect to investment analyzer"""
    # Blueprint is registered as 'investment_analyzer' with endpoint 'index'
    return redirect(url_for('investment_analyzer.index'))

@pro_tools.route('/mobile-trading')
@login_required
@unified_access_required
def mobile_trading():
    """Redirect to mobile trading"""
    return redirect(url_for('main.mobile_trading_redirect'))
