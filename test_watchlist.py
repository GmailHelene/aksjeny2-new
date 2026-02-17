#!/usr/bin/env python3
"""
Test script for watchlist functionality
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, db
from flask import url_for
import requests

def test_watchlist():
    """Test if watchlist works"""
    app = create_app()
    
    with app.app_context():
        # Find a test user
        test_user = User.query.filter_by(username='helene721').first()
        
        print("=== Watchlist Test ===")
        
        if not test_user:
            print("❌ No test user found")
            return False
            
        print(f"✓ Found test user: {test_user.username}")
        
        # Test watchlist URLs
        print("\n=== Testing Watchlist URLs ===")
        
        with app.test_client() as client:
            # Login as the test user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                
            # Test watchlist page
            response = client.get('/portfolio/watchlist')
            print(f"Watchlist page: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error accessing watchlist")
                print(f"Response: {response.data.decode()[:500]}...")
                return False
            else:
                print(f"✓ Successfully accessed watchlist")
                content = response.data.decode()
                
                if "Watchlist Error" in content:
                    print("❌ Watchlist shows error page")
                    return False
                elif "Din Watchlist" in content:
                    print("✓ Watchlist template loaded correctly")
                elif "Laster varsler" in content:
                    print("❌ Watchlist shows eternal loading")
                    return False
                else:
                    print("❓ Unknown watchlist state")
                    
        return True

if __name__ == "__main__":
    test_watchlist()