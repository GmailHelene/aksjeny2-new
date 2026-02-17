"""
Simple login/register fix for immediate production stability
"""

from flask import render_template, request, redirect, url_for, flash, session, make_response, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from sqlalchemy import text
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def simple_login():
    """Simplified login route that avoids complex form handling"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not password:
                flash('Brukernavn og passord er påkrevd', 'danger')
                return render_template('simple_login.html')
            
            # Import models dynamically to avoid import errors
            from app.models.user import User
            from app.extensions import db
            
            # Simple user lookup
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if user and user.check_password(password):
                # Clear session and login user
                session.clear()
                login_user(user, remember=True)
                
                # Set session flags
                session['user_logged_in'] = True
                session['user_id'] = user.id
                session.permanent = True
                
                flash('Du er nå logget inn!', 'success')
                logger.info(f'User logged in: {user.email}')
                
                return redirect(url_for('main.index'))
            else:
                flash('Ugyldig brukernavn eller passord', 'danger')
                logger.warning(f'Failed login attempt for: {username}')
                
        except Exception as e:
            logger.error(f'Login error: {e}')
            flash('En feil oppstod under innlogging', 'danger')
    
    return render_template('simple_login.html')

def simple_register():
    """Simplified register route that avoids complex form handling"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not email or not password:
                flash('Alle felter er påkrevd', 'danger')
                return render_template('simple_register.html')
            
            # Basic email validation
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                flash('Ugyldig e-postadresse', 'danger')
                return render_template('simple_register.html')
            
            # Import models dynamically
            from app.models.user import User
            from app.extensions import db
            
            # Check if user exists
            existing_user = User.query.filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    flash('E-post er allerede registrert', 'danger')
                else:
                    flash('Brukernavn er allerede tatt', 'danger')
                return render_template('simple_register.html')
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registrering fullført! Du kan nå logge inn.', 'success')
            logger.info(f'New user registered: {email}')
            
            return redirect(url_for('main.login'))
            
        except Exception as e:
            logger.error(f'Registration error: {e}')
            flash('En feil oppstod under registrering', 'danger')
            try:
                from app.extensions import db
                db.session.rollback()
            except:
                pass
    
    return render_template('simple_register.html')
