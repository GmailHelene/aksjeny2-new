#!/usr/bin/env python3
"""
Test script for test alert button
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, db

def test_alert_button():
    """Test test alert button functionality"""
    app = create_app()
    
    with app.app_context():
        test_user = User.query.filter_by(username='helene721').first()
        
        print("=== Test Alert Button Test ===")
        
        if not test_user:
            print("❌ No test user found")
            return False
            
        print(f"✓ Found test user: {test_user.username}")
        
        with app.test_client() as client:
            # Login as the test user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                
            # Test watchlist settings page loads
            response = client.get('/watchlist/settings')
            print(f"Watchlist settings page: {response.status_code}")
            
            if response.status_code == 200:
                content = response.data.decode()
                if "Send testvarsel" in content:
                    print("✓ Test alert button found in template")
                else:
                    print("❌ Test alert button not found in template")
                    return False
            
            # Test the test alert endpoint with proper session
            response = client.post('/watchlist/test-alert', 
                                 headers={'Content-Type': 'application/json'},
                                 json={})
            print(f"Test alert endpoint: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.get_json()
                    if data and data.get('success'):
                        print("✓ Test alert endpoint works correctly")
                        print(f"  Message: {data.get('message')}")
                        return True
                    else:
                        print(f"❌ Test alert failed: {data}")
                        return False
                except:
                    print(f"❌ Invalid JSON response from test alert endpoint")
                    print(f"Response: {response.data.decode()[:200]}...")
                    return False
            else:
                print(f"❌ Test alert endpoint returned status {response.status_code}")
                return False
                    
        return True

if __name__ == "__main__":
    test_alert_button()