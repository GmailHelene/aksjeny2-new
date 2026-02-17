#!/usr/bin/env python3
"""
Test script for insider trading page
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, db

def test_insider_trading():
    """Test insider trading page"""
    app = create_app()
    
    with app.app_context():
        test_user = User.query.filter_by(username='helene721').first()
        
        print("=== Insider Trading Test ===")
        
        if not test_user:
            print("❌ No test user found")
            return False
            
        print(f"✓ Found test user: {test_user.username}")
        
        with app.test_client() as client:
            # Login as the test user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                
            # Test insider trading page
            response = client.get('/analysis/insider-trading')
            print(f"Insider trading page: {response.status_code}")
            
            if response.status_code == 200:
                content = response.data.decode()
                
                if "ikke tilgjengelig" in content.lower() or "unavailable" in content.lower():
                    print("✓ Insider trading shows unavailable message correctly")
                    if "betalt API-abonnement" in content:
                        print("✓ Shows proper explanation about paid API requirement")
                    return True
                elif "Insiderhandel Intelligence" in content:
                    print("✓ Insider trading page loads with data")
                    return True
                else:
                    print("❓ Unknown insider trading page state")
                    print(f"Content preview: {content[:200]}...")
            else:
                print(f"❌ Error accessing insider trading page")
                print(f"Response: {response.data.decode()[:200]}...")
                return False
                    
        return True

if __name__ == "__main__":
    test_insider_trading()