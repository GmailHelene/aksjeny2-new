from flask import Blueprint, render_template, redirect, url_for, session, request
from flask_login import login_required, current_user
from flask_babel import Babel, get_locale

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    try:
        # Fix: Proper profile page handling
        user_data = {
            'email': current_user.email,
            'username': current_user.username,
            'created_at': current_user.created_at,
            'subscription': current_user.subscription_type or 'Free',
            'portfolios': current_user.portfolios.count(),
            'alerts': current_user.alerts.count()
        }
        return render_template('profile/index.html', user=user_data)
    except Exception as e:
        # Fallback if there's an error
        return render_template('profile/index.html', user=current_user)

@profile_bp.route('/set-language/<language>')
def set_language(language):
    """Fix for translation toggle"""
    if language in ['no', 'en']:
        session['language'] = language
        # Force page reload with new language
        return redirect(request.referrer or url_for('main.index'))
    return redirect(url_for('main.index'))

# Language selector helper
def get_locale():
    return session.get('language', 'no')

# Translation JavaScript fix
translation_js = """
// filepath: vscode-vfs://github%2B7b2276223a312c22726566223a7b2274797065223a342c226964223a226d6173746572227d7d/GmailHelene/aksjeny2/static/js/translation.js
document.addEventListener('DOMContentLoaded', function() {
    const langButton = document.querySelector('.language-toggle');
    if (langButton) {
        langButton.addEventListener('click', function(e) {
            e.preventDefault();
            const currentLang = document.documentElement.lang || 'no';
            const newLang = currentLang === 'no' ? 'en' : 'no';
            window.location.href = `/set-language/${newLang}`;
        });
    }
});
"""
