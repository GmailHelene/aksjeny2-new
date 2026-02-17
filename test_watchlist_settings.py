#!/usr/bin/env python3
"""
Test script for watchlist settings
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, db

def test_watchlist_settings():
    """Test if watchlist settings works"""
    app = create_app()
    
    with app.app_context():
        # Find a test user
        test_user = User.query.filter_by(username='helene721').first()
        
        print("=== Watchlist Settings Test ===")
        
        if not test_user:
            print("❌ No test user found")
            return False
            
        print(f"✓ Found test user: {test_user.username}")
        
        with app.test_client() as client:
            # Login as the test user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                
            # Test watchlist settings page
            response = client.get('/watchlist/settings')
            print(f"Watchlist settings page: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error accessing watchlist settings")
                print(f"Response: {response.data.decode()[:500]}...")
                return False
            else:
                content = response.data.decode()
                
                # Check if it's JSON or HTML
                if content.strip().startswith('{'):
                    print("❌ Watchlist settings returns JSON instead of HTML template")
                    print(f"JSON content: {content[:200]}...")
                    return False
                elif "Varslingsinnstillinger" in content or "watchlist" in content.lower():
                    print("✓ Watchlist settings template loaded correctly")
                    return True
                else:
                    print("❓ Unknown watchlist settings response")
                    print(f"Content preview: {content[:200]}...")
                    
        return True

if __name__ == "__main__":
    test_watchlist_settings()