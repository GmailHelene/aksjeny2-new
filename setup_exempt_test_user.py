"""
setup_exempt_test_user.py - Creates an exempt test user with premium access for testing purposes
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to the path to allow importing the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import create_app, db
    from app.models.user import User
    
    print("✅ Successfully imported the application")
except Exception as e:
    print(f"❌ Failed to import the application: {e}")
    sys.exit(1)

def create_exempt_test_user():
    """Creates an exempt test user with premium access"""
    try:
        app = create_app()
        
        with app.app_context():
            # Check if the test user already exists
            test_user = User.query.filter_by(email='test@aksjeradar.trade').first()
            
            if test_user:
                print("ℹ️ Exempt test user already exists - updating credentials and access")
            else:
                print("ℹ️ Creating new exempt test user")
                test_user = User(
                    email='test@aksjeradar.trade',
                    username='testuser',
                    is_admin=True,
                    trial_used=False
                )
                db.session.add(test_user)
            
            # Set password
            test_user.set_password('aksjeradar2024')
            
            # Set up as lifetime premium user
            test_user.has_subscription = True
            test_user.subscription_type = 'lifetime'
            test_user.subscription_start = datetime.utcnow()
            test_user.subscription_end = None
            test_user.is_admin = True
            test_user.trial_used = True
            
            # Make sure the user is verified if that attribute exists
            if hasattr(test_user, 'email_verified'):
                test_user.email_verified = True
            
            # Save changes
            db.session.commit()
            
            print("\n===== Test User Created =====")
            print("✅ Email: test@aksjeradar.trade")
            print("✅ Username: testuser")
            print("✅ Password: aksjeradar2024")
            print("✅ Premium: Yes (lifetime access)")
            print("✅ Is Admin: Yes")
            
    except Exception as e:
        print(f"❌ Failed to create exempt test user: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_exempt_test_user()
    if success:
        print("\n✅ Exempt test user created successfully!")
        print("This user is added to EXEMPT_EMAILS in access_control_unified.py")
        print("and will have full access to all premium features.")
    else:
        print("❌ Failed to create exempt test user")
        sys.exit(1)
