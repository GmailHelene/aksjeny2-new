from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from ..extensions import db
from ..services.performance_monitor import PerformanceMonitor
from ..models.user import User
from ..models.portfolio import Portfolio

admin = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn for å få tilgang til admin-siden.', 'error')
            return redirect(url_for('main.login'))
        
        # Check if user has admin rights - safe check
        is_admin = getattr(current_user, 'is_admin', False)
        if not is_admin:
            flash('Tilgang nektet. Admin-rettigheter kreves.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with system overview"""
    return render_template('admin/dashboard.html')

@admin.route('/performance')
@login_required
@admin_required
def performance_stats():
    """Vis ytelsesstatistikk"""
    try:
        monitor = PerformanceMonitor()
        
        # Hent statistikk for siste 24 timer
        stats = monitor.get_performance_stats(hours=24)
        
        # Hent feillog
        error_log = monitor.get_error_log(limit=50)
        
        return render_template('admin/performance.html', 
                             stats=stats, 
                             error_log=error_log)
    except Exception as e:
        flash(f'Feil ved henting av ytelsesstatistikk: {str(e)}', 'error')
        return render_template('admin/performance.html', 
                             stats={'total_requests': 0, 'avg_response_time': 0, 'error_count': 0, 'error_rate': 0, 'slowest_endpoints': [], 'most_used_endpoints': []}, 
                             error_log=[])

@admin.route('/api/performance')
@login_required
@admin_required
def api_performance_stats():
    """API for å hente ytelsesstatistikk"""
    try:
        monitor = PerformanceMonitor()
        hours = request.args.get('hours', 24, type=int)
        
        stats = monitor.get_performance_stats(hours=hours)
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin.route('/api/errors')
@login_required
@admin_required
def api_error_log():
    """API for å hente feillog"""
    monitor = PerformanceMonitor()
    limit = request.args.get('limit', 50, type=int)
    
    error_log = monitor.get_error_log(limit=limit)
    
    return jsonify({
        'success': True,
        'data': error_log
    })

@admin.route('/users')
@login_required
@admin_required
def user_management():
    """Brukerhåndtering"""
    # Dette kan utvides senere
    return render_template('admin/users.html')

@admin.route('/system')
@login_required
@admin_required
def system_status():
    """Systemstatus og helse"""
    return render_template('admin/system.html')

@admin.route('/fix-database')
def fix_database():
    """Emergency database fix endpoint - NO AUTH REQUIRED"""
    try:
        # Add missing columns
        missing_columns = [
            ('reports_used_this_month', 'INTEGER DEFAULT 0'),
            ('last_reset_date', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('is_admin', 'BOOLEAN DEFAULT FALSE'),
            ('reset_token', 'VARCHAR(100)'),
            ('reset_token_expires', 'TIMESTAMP'),
            ('language', 'VARCHAR(10) DEFAULT \'no\''),
            ('notification_settings', 'TEXT'),
            ('two_factor_enabled', 'BOOLEAN DEFAULT FALSE'),
            ('two_factor_secret', 'VARCHAR(32)'),
            ('email_verified', 'BOOLEAN DEFAULT TRUE'),
            ('is_locked', 'BOOLEAN DEFAULT FALSE'),
            ('last_login', 'TIMESTAMP'),
            ('login_count', 'INTEGER DEFAULT 0')
        ]
        
        results = []
        
        for column_name, column_def in missing_columns:
            try:
                # Use PostgreSQL's ADD COLUMN IF NOT EXISTS
                sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_def}"
                db.session.execute(text(sql))
                results.append(f"✅ Added column: {column_name}")
            except Exception as e:
                results.append(f"❌ Error adding {column_name}: {str(e)}")
        
        # Create test users
        test_users = [
            ('helene721', 'helene721@gmail.com', 'password123', True),
            ('eirik', 'eirik@example.com', 'password123', False),
            ('admin', 'admin@example.com', 'admin123', True)
        ]
        
        for username, email, password, is_admin in test_users:
            try:
                existing_user = User.query.filter(
                    (User.username == username) | (User.email == email)
                ).first()
                
                if existing_user:
                    existing_user.set_password(password)
                    existing_user.has_subscription = True
                    existing_user.subscription_type = 'monthly'
                    if hasattr(existing_user, 'is_admin'):
                        existing_user.is_admin = is_admin
                    if hasattr(existing_user, 'email_verified'):
                        existing_user.email_verified = True
                    results.append(f"✅ Updated user: {username}")
                else:
                    # Create minimal user first
                    user = User(
                        username=username,
                        email=email,
                        has_subscription=True,
                        subscription_type='monthly'
                    )
                    user.set_password(password)
                    
                    # Set additional fields if they exist
                    if hasattr(user, 'is_admin'):
                        user.is_admin = is_admin
                    if hasattr(user, 'email_verified'):
                        user.email_verified = True
                    if hasattr(user, 'reports_used_this_month'):
                        user.reports_used_this_month = 0
                    if hasattr(user, 'login_count'):
                        user.login_count = 0
                    if hasattr(user, 'language'):
                        user.language = 'no'
                    
                    db.session.add(user)
                    results.append(f"✅ Created user: {username}")
            except Exception as e:
                results.append(f"❌ Error with user {username}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Database fix completed',
            'results': results,
            'login_info': [
                'Username: helene721, Password: password123',
                'Username: eirik, Password: password123',
                'Username: admin, Password: admin123'
            ]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin.route('/test-login/<username>')
def test_login_user(username):
    """Test if user exists and can be queried - NO AUTH REQUIRED"""
    try:
        # Try to find user with minimal query
        user = db.session.execute(
            text("SELECT id, username, email FROM users WHERE username = :username LIMIT 1"),
            {'username': username}
        ).fetchone()
        
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user[0],
                    'username': user[1], 
                    'email': user[2]
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'User {username} not found'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
