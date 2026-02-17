#!/usr/bin/env python3
"""
Test script for subscription display
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, db

def test_subscription_display():
    """Test subscription display for test user"""
    app = create_app()
    
    with app.app_context():
        # Find a test user
        test_user = User.query.filter_by(username='helene721').first()
        
        print("=== Subscription Display Test ===")
        
        if not test_user:
            print("❌ No test user found")
            return False
            
        print(f"✓ Found test user: {test_user.username}")
        
        # Check user attributes
        print(f"User ID: {test_user.id}")
        print(f"has_subscription: {getattr(test_user, 'has_subscription', 'NOT DEFINED')}")
        print(f"subscription_type: {getattr(test_user, 'subscription_type', 'NOT DEFINED')}")
        print(f"subscription: {getattr(test_user, 'subscription', 'NOT DEFINED')}")
        
        # Update user to have premium subscription for testing
        if not getattr(test_user, 'has_subscription', False):
            print("Setting user as premium for testing...")
            try:
                # Try to set premium attributes
                if hasattr(test_user, 'has_subscription'):
                    test_user.has_subscription = True
                if hasattr(test_user, 'subscription_type'):
                    test_user.subscription_type = 'premium'
                db.session.commit()
                print("✓ User updated to premium")
            except Exception as e:
                print(f"❌ Error updating user: {e}")
                
        with app.test_client() as client:
            # Login as the test user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                
            # Test settings page for subscription display
            response = client.get('/settings')
            print(f"Settings page: {response.status_code}")
            
            if response.status_code == 200:
                content = response.data.decode()
                
                if "Premium" in content:
                    print("✓ Premium text found in settings")
                elif "Gratis plan" in content or "Free" in content:
                    print("❌ Shows 'Free' instead of 'Premium'")
                else:
                    print("❓ No subscription text found")
                    
                # Extract subscription info section
                if "Nåværende plan" in content:
                    start = content.find("Nåværende plan")
                    end = content.find("</div>", start + 300)
                    if end > start:
                        subscription_section = content[start:end]
                        print(f"Subscription section: {subscription_section[:200]}...")
                        
        return True

if __name__ == "__main__":
    test_subscription_display()