def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Du har ikke tilgang til denne siden', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import cache
import os
import shutil
import time
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Du har ikke tilgang til denne siden', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/clear-cache', methods=['POST'])
@admin_required
def clear_cache():
    """Clear all application caches"""
    try:
        # Clear Flask-Caching cache
        cache.clear()
        # Clear Python __pycache__ directories
        for root, dirs, files in os.walk(admin_bp.root_path):
            for dir in dirs:
                if dir == '__pycache__':
                    shutil.rmtree(os.path.join(root, dir))
        # Clear session cache
        from flask import current_app
        current_app.session_interface.cache.clear() if hasattr(current_app.session_interface, 'cache') else None
        # Clear static file cache by adding version parameter
        current_app.config['ASSETS_VERSION'] = str(int(time.time()))
        flash('All caches cleared successfully!', 'success')
        return jsonify({'success': True, 'message': 'All caches cleared'})
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Cache clearing error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/clear-browser-cache')
@admin_required  
def clear_browser_cache_instructions():
    """Return instructions for clearing browser cache"""
    return render_template('admin/clear_cache.html')
