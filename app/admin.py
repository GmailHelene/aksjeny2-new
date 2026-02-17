"""
Admin routes for Aksjeradar
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin tilgang kreves.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    return jsonify({
        'status': 'OK',
        'message': 'Admin dashboard',
        'user': current_user.email if current_user.is_authenticated else None
    })