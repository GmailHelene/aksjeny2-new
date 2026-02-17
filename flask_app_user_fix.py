"""
flask_app_user_fix.py - Creates and fixes user accounts through Flask app context
"""

from flask import Flask
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Subscription fields
    has_subscription = db.Column(db.Boolean, default=False)
    subscription_type = db.Column(db.String(20), default='free')
    subscription_start = db.Column(db.DateTime, nullable=True)
    subscription_end = db.Column(db.DateTime, nullable=True)
    trial_used = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

def fix_test_user_accounts():
    """Create or fix test user accounts"""
    # Test user data
    test_users = [
        {
            'email': 'test@aksjeradar.trade',
            'username': 'testuser',
            'password': 'aksjeradar2024'
        },
        {
            'email': 'investor@aksjeradar.trade',
            'username': 'investor',
            'password': 'aksjeradar2024'
        }
    ]
    
    with app.app_context():
        for user_data in test_users:
            email = user_data['email']
            username = user_data['username']
            password = user_data['password']
            
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if user:
                print(f"Updating existing user: {email}")
                
                # Update user data
                user.username = username
                user.password_hash = generate_password_hash(password)
                user.has_subscription = True
                user.subscription_type = 'lifetime'
                user.subscription_start = datetime.utcnow()
                user.subscription_end = None
                user.is_admin = True
                user.trial_used = True
            else:
                print(f"Creating new user: {email}")
                
                # Create new user
                user = User(
                    email=email,
                    username=username,
                    password_hash=generate_password_hash(password),
                    has_subscription=True,
                    subscription_type='lifetime',
                    subscription_start=datetime.utcnow(),
                    is_admin=True,
                    trial_used=True
                )
                db.session.add(user)
            
            # Commit changes for this user
            db.session.commit()
            print(f"User {email} saved successfully!")
        
        # Verify users
        print("\n===== VERIFICATION =====")
        for user_data in test_users:
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            
            if user:
                print(f"\nUser: {email}")
                print(f"- Username: {user.username}")
                print(f"- Has password hash: {'Yes' if user.password_hash else 'No'}")
                print(f"- Has subscription: {'Yes' if user.has_subscription else 'No'}")
                print(f"- Subscription type: {user.subscription_type}")
                print(f"- Is admin: {'Yes' if user.is_admin else 'No'}")
                
                # Create verification file for this user
                with open(f"user_{user.username}_verified.txt", 'w') as f:
                    f.write(f"User {email} verified successfully!\n")
                    f.write(f"Username: {user.username}\n")
                    f.write(f"Password: {user_data['password']}\n")
                    f.write(f"Has subscription: {'Yes' if user.has_subscription else 'No'}\n")
                    f.write(f"Subscription type: {user.subscription_type}\n")
                    f.write(f"Is admin: {'Yes' if user.is_admin else 'No'}\n")
                    f.write(f"\nCreated at: {datetime.utcnow()}\n")
            else:
                print(f"User {email} not found - verification failed!")

if __name__ == "__main__":
    print("===== FLASK APP USER FIX =====")
    
    try:
        fix_test_user_accounts()
        print("\n✅ User fix completed successfully!")
        print("Verification files have been created for each user.")
        print("Please restart the Flask server before trying to login again.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
