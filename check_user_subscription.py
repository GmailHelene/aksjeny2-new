#!/usr/bin/env python3
"""
Check user subscription status
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, db

def check_user_subscription():
    """Check user subscription details"""
    app = create_app()
    
    with app.app_context():
        test_user = User.query.filter_by(username='helene721').first()
        
        if not test_user:
            print("❌ No test user found")
            return
            
        print(f"=== User: {test_user.username} ===")
        
        # Check all user attributes
        for attr in dir(test_user):
            if 'subscription' in attr.lower() or 'premium' in attr.lower():
                try:
                    value = getattr(test_user, attr)
                    if not callable(value):
                        print(f"{attr}: {value}")
                except:
                    print(f"{attr}: <error getting value>")
                    
        # Also check User model attributes
        print("\n=== User Model Attributes ===")
        from app.models.user import User as UserModel
        for column in UserModel.__table__.columns:
            column_name = column.name
            if 'subscription' in column_name.lower() or 'premium' in column_name.lower():
                value = getattr(test_user, column_name, 'NOT FOUND')
                print(f"DB Column {column_name}: {value}")

if __name__ == "__main__":
    check_user_subscription()