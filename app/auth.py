from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User
from app.forms import LoginForm, RegistrationForm

# Emails that are explicitly blocked from logging in
# Use lowercase comparison for safety
BLOCKED_EMAILS = {
    'eiriktollan.berntsen@gmail.com',
    'eirik@example.com',
}

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        # Check if there's a next parameter to redirect to
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Blocked login check
            try:
                if (user.email or '').strip().lower() in BLOCKED_EMAILS:
                    flash('Denne kontoen er deaktivert. Kontakt support hvis du mener dette er feil.', 'warning')
                    return redirect(url_for("auth.login"))
            except Exception:
                # If something goes wrong with the check, do not allow login
                flash('Innlogging blokkert for denne kontoen.', 'warning')
                return redirect(url_for("auth.login"))
            login_user(user, remember=form.remember_me.data)
            
            # Track login achievement
            try:
                from app.models.achievements import UserStats
                user_stats = UserStats.query.filter_by(user_id=user.id).first()
                if not user_stats:
                    user_stats = UserStats(user_id=user.id)
                    db.session.add(user_stats)
                user_stats.update_consecutive_logins()
                db.session.commit()
            except Exception as e:
                # Don't fail login if achievement tracking fails
                pass
            
            # Redirect to next page after successful login
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)

@auth.route("/logout")
def logout():
    """Logout is idempotent and allowed for anonymous users.

    If a user is authenticated, logs them out. In all cases, redirect to
    homepage so tests following redirects end on a 200 OK page.
    """
    try:
        if current_user.is_authenticated:
            logout_user()
    except Exception:
        # Do not fail logout on any error
        pass
    return redirect(url_for("main.index"))

@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        # Check if there's a next parameter to redirect to
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! You can now log in.", "success")
        # Pass next parameter to login page
        next_page = request.args.get('next')
        if next_page:
            return redirect(url_for("auth.login", next=next_page))
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)

@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Nåværende passord er feil.', 'error')
            return render_template('change_password.html')
            
        # Validate new password
        if new_password != confirm_password:
            flash('De nye passordene stemmer ikke overens.', 'error')
            return render_template('change_password.html')
            
        if len(new_password) < 6:
            flash('Passord må være minst 6 tegn.', 'error')
            return render_template('change_password.html')
            
        # Update password
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Passord oppdatert!', 'success')
            return redirect(url_for('main.settings'))
        except Exception as e:
            flash('Feil ved oppdatering av passord.', 'error')
            db.session.rollback()
            
    return render_template('change_password.html')


